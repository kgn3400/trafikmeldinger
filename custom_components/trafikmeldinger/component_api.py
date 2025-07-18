"""Component api for Trafikmeldinger."""

from asyncio import timeout
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from logging import Logger
from re import IGNORECASE, Pattern, compile, escape

from aiohttp.client import ClientSession
from babel.dates import format_timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    CONF_MATCH_CASE,
    CONF_MATCH_LIST,
    CONF_MATCH_WORD,
    CONF_MAX_ROW_FETCH,
    CONF_MAX_TIME_BACK,
    CONF_MAX_TIME_BACK_CONCLUDED,
    CONF_ONLY_SHOW_LAST_UPDATE,
    CONF_REGION,
    CONF_REGION_ALL,
    CONF_SUM_INCL_IMPORTANT_NOTICES,
    CONF_SUM_INCL_LATEST_TRAFFIC_REPORT,
    CONF_SUM_INCL_PREVIOUS_TRAFFIC_REPORTS,
    CONF_TRANSPORT_TYPE,
    CONF_TRANSPORT_TYPE_ALL,
    CONF_TRANSPORT_TYPE_PRIVATE,
    DICT_REGION,
    DICT_TRANSPORT_TYPE,
    DOMAIN,
    EVENT_NEW_IMPORTANT_NOTICE,
    EVENT_NEW_TRAFFIC_REPORT,
    STORAGE_KEY,
    STORAGE_VERSION,
)

# from .storage_json import StorageJson
from .hass_util import StorageJson, async_hass_add_executor_job, handle_retries


# ------------------------------------------------------
# ------------------------------------------------------
@dataclass
class TrafficStorage(StorageJson):
    """TrafficStorage."""

    # ------------------------------------------------------
    def __init__(self, hass: HomeAssistant) -> None:
        """Init."""

        super().__init__(hass, STORAGE_KEY, STORAGE_VERSION)

        self.traffic_reports_last_id: dict[str, str] = {}
        self.important_notice_last_id: str = ""

        self.marked_as_read: int = 0


# ------------------------------------------------------------------
# ------------------------------------------------------------------
@dataclass
class ComponentApi:
    """Trafikmeldinger interface."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        session: ClientSession | None,
    ) -> None:
        """Trafikmeldinger api."""

        self.hass: HomeAssistant = hass
        self.entry: ConfigEntry = entry
        self.session: ClientSession | None = session

        self.traffic_reports: list = []
        self.important_notices: list = []
        self.sum_traffic_md: str = ""

        self.close_session: bool = False

        self.request_timeout: int = 10
        self.storage: TrafficStorage = TrafficStorage(hass)

        self.regex_comp: Pattern | None = None
        self.traffic_report_rotate_pos: int = -1

        self.regex_comp = self.compile_any_word_regex(
            entry.options.get(CONF_MATCH_LIST),
            entry.options.get(CONF_MATCH_WORD, False),
            entry.options.get(CONF_MATCH_CASE, False),
        )

        self._max_time_back: datetime = None
        self._max_time_back_concluded: datetime = None

    # ------------------------------------------------------------------
    def compile_any_word_regex(
        self,
        words: list[str],
        use_word_boundaries: bool = True,
        case_sensitive: bool = False,
    ) -> Pattern[str] | None:
        """Returns a compiled regex pattern that matches if ANY word in the list is present in a text.

        - use_word_boundaries: If True, only matches whole words.
        - case_sensitive: If False, matches regardless of letter case.
        """

        if len(words) == 0:
            return None

        if use_word_boundaries:
            pattern = r"|".join(
                rf"\b{escape(word)}\b" for word in words if word.strip() != ""
            )
        else:
            pattern = r"|".join(escape(word) for word in words if word.strip() != "")
        combined_pattern: str = f"({pattern})"
        flags: int = 0 if case_sensitive else IGNORECASE
        return compile(combined_pattern, flags)

    # ------------------------------------------------------------------
    @async_hass_add_executor_job()
    def relative_time(self, iso_datetime: str) -> str:
        """Relative time."""

        diff: timedelta = datetime.fromisoformat(iso_datetime) - dt_util.now()

        return format_timedelta(diff, add_direction=True, locale="da")

    # ------------------------------------------------------
    def traffic_report_format(self, report: dict) -> str:
        """Format traffic report."""

        if report.get("concluded", False):
            return "Afsluttet -" + report["text"][:243]
        return report["text"][:255]

    # ------------------------------------------------------
    def traffic_report_updates_format(self, report: dict) -> list:
        """Format traffic report updates."""

        if report.get("updates") is not None:
            tmp_list: list = [x["text"] for x in report["updates"]]
            return tmp_list

        return {}

    # ------------------------------------------------------
    async def async_traffic_report_format_md(self, report: dict) -> str:
        """Format traffic report as markdown."""

        tmp_md: str = ""

        if report.get("concluded", False):
            tmp_color: str = "green"
        else:
            tmp_color = "red"

        if report["type"] == CONF_TRANSPORT_TYPE_PRIVATE:
            tmp_md = (
                "###  <font color="
                + tmp_color
                + '> <ha-icon icon="mdi:car"></ha-icon></font> '
            )
        else:
            tmp_md = (
                "###  <font color="
                + tmp_color
                + '> <ha-icon icon="mdi:train-bus"></ha-icon></font> '
            )

        tmp_md += DICT_REGION[report["region"]]

        tmp_md += " " + await self.relative_time(report["createdTime"])

        if report.get("concluded", False):
            tmp_md += "\n\n**Afsluttet** - " + report["text"]
        else:
            tmp_md += "\n\n" + report["text"]

        if report.get("updates") is not None and len(report["updates"]) > 0:
            if self.entry.options.get(CONF_ONLY_SHOW_LAST_UPDATE, True):
                tmp_md += (
                    "\n\n>"
                    + datetime.fromisoformat(
                        report["updates"][0]["createdTime"]
                    ).strftime("Kl. %H.%M: ")
                    + str(report["updates"][0]["text"]).replace("\n\n", "\n")
                )

            else:
                for update in report["updates"]:
                    tmp_md += (
                        "\n\n>"
                        + datetime.fromisoformat(update["createdTime"]).strftime(
                            "Kl. %H.%M: "
                        )
                        + str(update["text"]).replace("\n\n", "\n")
                    )

        return tmp_md

    # ------------------------------------------------------
    def important_notice_format(self, report: dict) -> str:
        """Format important notice."""

        return report["text"][:255]

    # ------------------------------------------------------
    async def async_important_notice_format_md(self, report: dict) -> str:
        """Format important notice as markdown."""

        tmp_md: str = '###  <font color=red> <ha-icon icon="mdi:exclamation-thick"></ha-icon></font> '

        tmp_md += " Vigtig meddelelse " + str(
            await self.relative_time(report["updatedTime"])
        )

        tmp_md += "\n\n" + report["text"]

        return tmp_md

    # ------------------------------------------------------
    async def async_formatted_traffic_reports(self) -> None:
        """Format traffic reports."""

        for report in self.traffic_reports:
            report["formated_text"] = self.traffic_report_format(report)
            report["formated_updates_text"] = self.traffic_report_updates_format(report)
            report["markdown"] = await self.async_traffic_report_format_md(report)

    # ------------------------------------------------------
    async def async_formatted_important_notices(self) -> None:
        """Format notices."""

        for notice in self.important_notices:
            notice["formated_text"] = self.important_notice_format(notice)
            notice["markdown"] = await self.async_important_notice_format_md(notice)

    # ------------------------------------------------------
    async def async_update_important_notice_last_event_id(self) -> None:
        """Update important notice last event id."""

        if len(self.important_notices) == 0:
            self.storage.important_notice_last_id = ""
            await self.storage.async_write_settings()
        elif self.storage.important_notice_last_id != (
            self.important_notices[0]["_id"]
            + " "
            + self.important_notices[0]["updatedTime"]
        ):
            self.storage.important_notice_last_id = (
                self.important_notices[0]["_id"]
                + " "
                + self.important_notices[0]["updatedTime"]
            )

            await self.storage.async_write_settings()

    # ------------------------------------------------------
    async def async_traffic_reports_event_fire(self) -> str:
        """Traffic report event fire."""

        # ---------------------
        async def _fire_event(report: dict) -> str:
            if report.get("updates") is not None and len(report["updates"]) > 0:
                tmp_updated_time: str = report["updates"][0]["createdTime"]
            else:
                tmp_updated_time = report["updatedTime"]

            if (
                self.storage.traffic_reports_last_id.get(report["_id"], "")
                != tmp_updated_time
            ):
                self.hass.bus.async_fire(
                    DOMAIN + "." + EVENT_NEW_TRAFFIC_REPORT,
                    {
                        "ny_melding": report["text"],
                        "opdateringer": report["formated_updates_text"],
                        "region": DICT_REGION[report["region"]],
                        "transporttype": DICT_TRANSPORT_TYPE[report["type"]],
                        "oprettet_tidspunkt": report["createdTime"],
                        "opdateret_tidspunkt": report["updatedTime"],
                    },
                )
                return tmp_updated_time

            return ""

        # ---------------------

        update_stg: bool = False

        if len(self.traffic_reports) == 0:
            return False

        for report in reversed(self.traffic_reports):
            if report.get("concluded", True):
                if self.storage.traffic_reports_last_id.get(report["_id"], "") == "":
                    continue

                await _fire_event(report)

                self.storage.traffic_reports_last_id.pop(report["_id"], None)
                update_stg = True

            else:
                tmp_updated_time = await _fire_event(report)

                if tmp_updated_time != "":
                    self.storage.traffic_reports_last_id[report["_id"]] = (
                        tmp_updated_time
                    )
                    update_stg = True

        return update_stg

    # ------------------------------------------------------
    async def async_important_notice_event_fire(self) -> None:
        """Fire important notice event."""

        if len(self.important_notices) == 0:
            return

        if self.storage.important_notice_last_id != (
            self.important_notices[0]["_id"]
            + " "
            + self.important_notices[0]["updatedTime"]
        ):
            self.hass.bus.async_fire(
                DOMAIN + "." + EVENT_NEW_IMPORTANT_NOTICE,
                {
                    "ny_melding": self.important_notices[0]["text"],
                    "oprettet_tidspunkt": self.important_notices[0]["createdTime"],
                    "opdateret_tidspunkt": self.important_notices[0]["updatedTime"],
                },
            )
        await self.async_update_important_notice_last_event_id()

    # ------------------------------------------------------
    # def set_max_time_back(self) -> None:
    #     """Set max time back."""

    #     if self.entry.options.get(CONF_MAX_TIME_BACK, 0) > 0:
    #         self._max_time_back: datetime = dt_util.as_local(
    #             datetime.now(UTC)
    #         ) - timedelta(hours=self.entry.options[CONF_MAX_TIME_BACK])

    #     else:
    #         self._max_time_back = None

    #     self._max_time_back_concluded: datetime = dt_util.as_local(
    #         datetime.now(UTC)
    #     ) - timedelta(hours=self.entry.options.get(CONF_MAX_TIME_BACK_CONCLUDED, 2))

    # ------------------------------------------------------
    async def async_create_sum_traffic_md(self) -> None:
        """Create sum traffic."""

        self.sum_traffic_md = ""

        if self.important_notices and self.entry.options.get(
            CONF_SUM_INCL_IMPORTANT_NOTICES, True
        ):
            self.sum_traffic_md += self.important_notices[0]["markdown"]

        if self.traffic_reports and self.entry.options.get(
            CONF_SUM_INCL_LATEST_TRAFFIC_REPORT, True
        ):
            if self.sum_traffic_md:
                self.sum_traffic_md += "\n___\n"
            self.sum_traffic_md += (
                "### Seneste trafikmelding:\n" + self.traffic_reports[0]["markdown"]
            )

        if (
            self.traffic_reports
            and self.traffic_report_rotate_pos > 0
            and self.entry.options.get(CONF_SUM_INCL_PREVIOUS_TRAFFIC_REPORTS, True)
        ):
            if self.sum_traffic_md:
                self.sum_traffic_md += "\n___\n"
            self.sum_traffic_md += (
                "### Tidligere trafikmelderinger:\n"
                + self.traffic_reports[self.traffic_report_rotate_pos]["markdown"]
            )

        if self.sum_traffic_md:
            self.sum_traffic_md = "## Trafikmeldinger:\n" + self.sum_traffic_md
        else:
            self.sum_traffic_md = "## Trafikmeldinger:\nIngen aktuelle trafikmeldinger"

    # ------------------------------------------------------
    async def async_refresh_traffic_reports(self) -> None:
        """Refresh traffic report."""

        if self.session is None:
            self.session = ClientSession()
            self.close_session = True

        # self.set_max_time_back()

        tmp_result: bool = await self.async_get_new_traffic_reports()

        await self.async_formatted_traffic_reports()

        if self.session and self.close_session:
            await self.session.close()

        if await self.async_remove_to_old_traffic_reports():
            tmp_result = True

        if await self.async_traffic_reports_event_fire():
            tmp_result = True

        await self.async_create_sum_traffic_md()

        if tmp_result:
            await self.storage.async_write_settings()

    # ------------------------------------------------------
    async def async_refresh_important_notices(self) -> bool:
        """Refresh important notices."""

        if self.session is None:
            self.session = ClientSession()
            self.close_session = True

        # self.set_max_time_back()

        tmp_result: bool = await self.async_get_important_notices()
        await self.async_formatted_important_notices()

        if self.session and self.close_session:
            await self.session.close()

        if tmp_result:
            await self.storage.async_write_settings()

        return tmp_result

    # ------------------------------------------------------
    async def async_is_match_traffic_report(self, check_report: dict) -> bool:
        """Check of traffic report is a match."""

        if self.regex_comp is None:
            return True

        tmp_txt: str = check_report["text"]

        if check_report.get("reference") is not None:
            tmp_txt += check_report["reference"]["text"]

        if self.regex_comp.search(tmp_txt):
            return True
        return False

    # ------------------------------------------------------
    async def async_is_old_report(self, check_report: dict) -> bool:
        """Check of traffic report is to old."""

        # tmp_rep_time = dt_util.as_local(
        #     datetime.fromisoformat(check_report.get("updatedTime"))
        # ) + timedelta(hours=self.entry.options.get(CONF_MAX_TIME_BACK, 0))

        # tmp_now = dt_util.as_local(datetime.now(UTC))

        if (
            dt_util.as_local(datetime.fromisoformat(check_report.get("updatedTime")))
            + timedelta(hours=self.entry.options.get(CONF_MAX_TIME_BACK, 0))
        ) < dt_util.as_local(datetime.now(UTC)):
            return True

        if check_report.get("concluded", False) is True:
            if (
                dt_util.as_local(
                    datetime.fromisoformat(check_report.get("updatedTime"))
                )
                + timedelta(
                    hours=self.entry.options.get(CONF_MAX_TIME_BACK_CONCLUDED, 2)
                )
            ) < dt_util.as_local(datetime.now(UTC)):
                return True

        return False

        # if (
        #     self._max_time_back is not None
        #     and datetime.fromisoformat(check_report["updatedTime"])
        #     < self._max_time_back
        # ):
        #     return True

        # if check_report.get("concluded", False) is True:
        #     if (
        #         datetime.fromisoformat(check_report["updatedTime"])
        #         < self._max_time_back_concluded
        #     ):
        #         return True

    # ------------------------------------------------------
    async def async_remove_to_old_traffic_reports(self) -> bool:
        """Remove to old traffic report."""

        ret_result: bool = False

        # Remove reports older than max_time_back
        if self.entry.options.get(CONF_MAX_TIME_BACK, 0) > 0:
            for idx, report in reversed(list(enumerate(self.traffic_reports))):
                if await self.async_is_old_report(report):
                    self.traffic_reports.pop(idx)
                    # self.traffic_reports.remove(report)
                    ret_result = True

            if len(self.traffic_reports) == 0:
                self.traffic_report_rotate_pos = -1
            elif self.traffic_report_rotate_pos >= len(self.traffic_reports):
                self.traffic_report_rotate_pos = 0

        return ret_result

    # ------------------------------------------------------
    def prepare_traffic_reports(self, reports: list) -> list:
        """Prepare traffic reports."""

        for tmp_report in reports:
            tmp_report["region"] = str(tmp_report["region"]).lower().replace("-", "_")
            tmp_report["type"] = str(tmp_report["type"]).lower().replace("-", "_")

            tmp_report["createdTime"] = (
                dt_util.as_local(datetime.fromisoformat(tmp_report["createdTime"]))
            ).isoformat()
            tmp_report["updatedTime"] = (
                dt_util.as_local(datetime.fromisoformat(tmp_report["updatedTime"]))
            ).isoformat()

            if tmp_report.get("updates") is not None:
                for tmp_update in tmp_report["updates"]:
                    tmp_update["createdTime"] = dt_util.as_local(
                        datetime.fromisoformat(tmp_update["createdTime"])
                    ).isoformat()

        return reports

    # ------------------------------------------------------
    @handle_retries(retries=5, retry_delay=5)
    async def _async_get_new_traffic_reports(self, traffic_report_url: str) -> list:
        async with timeout(self.request_timeout):
            response = await self.session.get(traffic_report_url)
            tmp_json: list = await response.json()

        return tmp_json

    # ------------------------------------------------------
    async def async_get_new_traffic_reports(self, last_entry_date: str = "") -> bool:
        """Get new traffic report."""

        done: bool = False
        ret_result: bool = False

        max_row_fetch: int = int(self.entry.options.get(CONF_MAX_ROW_FETCH, 0))

        if max_row_fetch == 0:
            max_row_fetch = 40

        region_part_url: str = ""
        transport_type_part_url: str = ""

        region: list = self.entry.options.get(CONF_REGION, [])

        reg: str
        for reg in region:
            if reg != CONF_REGION_ALL:
                region_part_url += f"regions%5B%5D={reg.upper().replace('_', '-')}&"

        transport_type: list = self.entry.options.get(CONF_TRANSPORT_TYPE, [])

        for reg in transport_type:
            if reg != CONF_TRANSPORT_TYPE_ALL:
                transport_type_part_url += (
                    f"type%5B%5D={reg.upper().replace('_', '-')}&"
                )

        traffic_report_url: str = f"https://api.dr.dk/trafik/posts?{region_part_url}{transport_type_part_url}lastPostDate={last_entry_date}"

        try:
            tmp_json: list = await self._async_get_new_traffic_reports(
                traffic_report_url
            )

        except TimeoutError:
            return False
        except Exception as e:  # noqa: BLE001
            Logger.error(f"Error fetching traffic reports: {e}")
            return False

        if len(tmp_json) == 0:
            return False

        last_entry_date = tmp_json[-1]["createdTime"]

        tmp_json = self.prepare_traffic_reports(tmp_json)

        if await self.async_is_old_report(tmp_json[0]):
            return False

        tmp_report: dict

        for tmp_report in tmp_json:
            id_found: bool = False

            for idx, report in enumerate(self.traffic_reports):
                if report["_id"] == tmp_report["_id"]:
                    id_found = True
                    tmp_read: bool = report.get("read", False)
                    self.traffic_reports[idx] = tmp_report
                    self.traffic_reports[idx]["read"] = tmp_read
                    break

            if id_found:
                continue

            if await self.async_is_old_report(
                tmp_report
            ) is False and await self.async_is_match_traffic_report(tmp_report):
                tmp_report["read"] = False
                self.traffic_reports.append(tmp_report)
                ret_result = True

        self.traffic_reports.sort(key=lambda x: x["updatedTime"], reverse=True)

        if max_row_fetch > 0 and len(self.traffic_reports) > max_row_fetch:
            done = True

            for _ in range(len(self.traffic_reports) - max_row_fetch):
                self.traffic_reports.pop()

        if not done:
            if await self.async_get_new_traffic_reports(last_entry_date) is True:
                ret_result = True

        return ret_result

    # ------------------------------------------------------
    @handle_retries(retries=5, retry_delay=5)
    async def _async_get_important_notices(self, important_notices_url: str) -> list:
        async with timeout(self.request_timeout):
            response = await self.session.get(important_notices_url)
            tmp_json: list = await response.json()

        return tmp_json

    # ------------------------------------------------------
    async def async_get_important_notices(self) -> bool:
        """Get important notices."""

        ret_result: bool = False

        important_notices_url: str = "https://api.dr.dk/trafik/notices"

        try:
            tmp_json: list = await self._async_get_important_notices(
                important_notices_url
            )

        except TimeoutError:
            return False
        except Exception as e:  # noqa: BLE001
            Logger.error(f"Error fetching important notices: {e}")
            return False

        if len(tmp_json) == 0:
            self.important_notices.clear()
            return False

        for tmp_notice in reversed(tmp_json):
            id_found: bool = False

            for report in self.important_notices:
                if (report["_id"] + report["updatedTime"]) == (
                    tmp_notice["_id"] + tmp_notice["updatedTime"]
                ):
                    id_found = True
                    break

            if id_found:
                continue

            self.important_notices.insert(0, tmp_notice)
            self.important_notices[0]["read"] = False
            ret_result = True

        # Remove important notices older than max_time_back
        if self.entry.options.get(CONF_MAX_TIME_BACK, 0) > 0:
            for idx, report in reversed(list(enumerate(self.important_notices))):
                if await self.async_is_old_report(report):
                    self.important_notices.pop(idx)
                    # self.important_notices.remove(report)
                    # ret_result = True

        return ret_result

    # ------------------------------------------------------
    def get_read_count(self, reports: list) -> int:
        """Get read count."""
        x: int = len([report for report in reports if report.get("read", False)])
        return x

    # ------------------------------------------------------------------
    def mark_all_traffic_reports_as_read(self) -> None:
        """Mark all traffic reports as read."""

        for report in self.traffic_reports:
            self.mark_traffic_report_as_read(report)

        self.storage.marked_as_read = len(self.traffic_reports)

    # ------------------------------------------------------------------
    def unmark_all_traffic_reports_as_read(self) -> None:
        """Unmark all traffic reports as read."""

        for report in self.traffic_reports:
            self.unmark_traffic_report_as_read(report)

        self.storage.marked_as_read = len(self.traffic_reports)

    # ------------------------------------------------------------------
    def mark_traffic_report_as_read(self, report: dict | int) -> None:
        """Mark report as read."""

        if isinstance(report, dict):
            report["read"] = True
        elif isinstance(report, int) and report < len(self.traffic_reports):
            self.traffic_reports[report]["read"] = True

    # ------------------------------------------------------------------
    def unmark_traffic_report_as_read(self, report: dict | int) -> None:
        """Unmark report as read."""

        if isinstance(report, dict):
            report["read"] = False
        elif isinstance(report, int) and report < len(self.traffic_reports):
            self.traffic_reports[report]["read"] = False

    # ------------------------------------------------------------------
    def mark_current_traffic_report_as_read(self) -> None:
        """Mark report as read."""

        if self.traffic_report_rotate_pos > -1:
            self.traffic_reports[self.traffic_report_rotate_pos]["read"] = True

        self.storage.marked_as_read = self.get_read_count(self.traffic_reports)

    # ------------------------------------------------------------------
    def unmark_current_traffic_report_as_read(self) -> None:
        """Unmark report as read."""

        if self.traffic_report_rotate_pos > -1:
            self.traffic_reports[self.traffic_report_rotate_pos]["read"] = False

        self.storage.marked_as_read = self.get_read_count(self.traffic_reports)

    # ------------------------------------------------------------------
    def mark_all_important_notices_as_read(self) -> None:
        """Mark all traffic reports as read."""

        for report in self.important_notices:
            self.mark_important_notice_as_read(report)

    # ------------------------------------------------------------------
    def unmark_all_important_notices_as_read(self) -> None:
        """Unmark all traffic reports as read."""

        for report in self.important_notices:
            self.unmark_important_notice_as_read(report)

    # ------------------------------------------------------------------
    def mark_important_notice_as_read(self, report: dict | int) -> None:
        """Mark report as read."""

        if isinstance(report, dict):
            report["read"] = True
        elif isinstance(report, int) and report < len(self.important_notices):
            self.important_notices[report]["read"] = True

    # ------------------------------------------------------------------
    def unmark_important_notice_as_read(self, report: dict | int) -> None:
        """Unmark report as read."""

        if isinstance(report, dict):
            report["read"] = False
        elif isinstance(report, int) and report < len(self.important_notices):
            self.important_notices[report]["read"] = False

    # ------------------------------------------------------------------
    def get_next_traffic_report_pos(self, start_pos: int = 0) -> int:
        """Get next traffic report position."""

        if (
            len(self.traffic_reports) == 0
            or all(value.get("read", False) for value in self.traffic_reports)
            or (len(self.traffic_reports) - 1) < start_pos
        ):
            self.traffic_report_rotate_pos = -1

        # elif len(self.traffic_reports) == 1:
        #     self.traffic_report_rotate_pos = 0
        else:
            if self.traffic_report_rotate_pos == -1:
                self.traffic_report_rotate_pos = start_pos - 1

            self.traffic_report_rotate_pos += 1

            if self.traffic_report_rotate_pos > (len(self.traffic_reports) - 1):
                self.traffic_report_rotate_pos = start_pos

            if self.traffic_reports[self.traffic_report_rotate_pos].get("read", False):
                self.get_next_traffic_report_pos(start_pos)

        return self.traffic_report_rotate_pos

    # ------------------------------------------------------------------
    def get_prev_traffic_report_pos(self, start_pos: int = 0) -> int:
        """Get previous traffic report position."""

        if (
            len(self.traffic_reports) == 0
            or all(value.get("read", False) for value in self.traffic_reports)
            or (len(self.traffic_reports) - 1) < start_pos
        ):
            self.traffic_report_rotate_pos = -1

        # elif len(self.traffic_reports) == 1:
        #     self.traffic_report_rotate_pos = 0
        else:
            self.traffic_report_rotate_pos -= 1

            if self.traffic_report_rotate_pos < start_pos:
                self.traffic_report_rotate_pos = len(self.traffic_reports) - 1

            if self.traffic_reports[self.traffic_report_rotate_pos].get("read", False):
                self.get_prev_traffic_report_pos(start_pos)

        return self.traffic_report_rotate_pos
