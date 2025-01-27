"""Component api for Trafikmeldinger."""

from asyncio import timeout
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial
from re import IGNORECASE, compile

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
    CONF_REGION,
    CONF_REGION_ALL,
    CONF_TRANSPORT_TYPE,
    CONF_TRANSPORT_TYPE_ALL,
    CONF_TRANSPORT_TYPE_PRIVATE,
    DICT_REGION,
)


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

        self.supress_update_listener: bool = False

        self.close_session: bool = False

        self.request_timeout: int = 10
        self.traffic_reports: list = []
        self.importan_notices: list = []

        self.regex_comp = None
        self.traffic_report_rotate_pos: int = -1

        if len(entry.options.get(CONF_MATCH_LIST, [])) > 0:
            match_word: str = r"\b" if entry.options.get(CONF_MATCH_WORD, False) else ""
            match_list: list[str] = entry.options.get(CONF_MATCH_LIST)
            reg1 = match_list[0]

            for reg in match_list[1:]:
                reg1 += "|" + reg
            regx = rf"{match_word}({reg1}){match_word}"

            self.regex_comp = (
                compile(regx)
                if entry.options.get(CONF_MATCH_CASE, False)
                else compile(regx, IGNORECASE)
            )

        self.max_time_back: datetime = None

        if self.entry.options.get(CONF_MAX_TIME_BACK, 0) > 0:
            self.max_time_back: datetime = dt_util.as_local(
                dt_util.now() - timedelta(hours=self.entry.options[CONF_MAX_TIME_BACK])
            )

    # ------------------------------------------------------------------
    async def async_relative_time(self, iso_datetime: str) -> str:
        """Relative time."""

        now = dt_util.now()
        diff: timedelta = datetime.fromisoformat(iso_datetime) - now
        # diff: timedelta = dt_util.as_local(datetime.fromisoformat(iso_datetime)) - now

        diff_str: str = await self.hass.async_add_executor_job(
            partial(
                format_timedelta,
                delta=diff,
                add_direction=True,
                locale="da",
            )
        )
        return diff_str

    # ------------------------------------------------------
    async def async_traffic_report_format(self, report: dict) -> str:
        """Format traffic report."""

        return report["text"][:255]

    # ------------------------------------------------------
    async def async_traffic_report_ref_format(self, report: dict) -> str:
        """Format traffic report reference."""

        if report.get("reference") is not None:
            return report["reference"]["text"][:255]

        return ""

    # ------------------------------------------------------
    async def async_traffic_report_format_md(self, report: dict) -> str:
        """Format traffic report as markdown."""

        tmp_md: str = ""

        if report["type"] == CONF_TRANSPORT_TYPE_PRIVATE:
            tmp_md = '###  <font color=red> <ha-icon icon="mdi:car"></ha-icon></font> '
        else:
            tmp_md = (
                '###  <font color=red> <ha-icon icon="mdi:train-bus"></ha-icon></font> '
            )

        tmp_md += DICT_REGION[report["region"]]

        tmp_md += " " + await self.async_relative_time(report["createdTime"])

        tmp_md += "\n\n" + report["text"]

        if report.get("reference") is not None:
            tmp_md += "\n\n>" + str(report["reference"]["text"]).replace("\n\n", "\n")

        return tmp_md

    # ------------------------------------------------------
    async def async_important_notice_format(self, report: dict) -> str:
        """Format important notice."""

        return report["text"][:255]

    # ------------------------------------------------------
    async def async_important_notice_format_md(self, report: dict) -> str:
        """Format important notice as markdown."""

        tmp_md: str = '###  <font color=red> <ha-icon icon="mdi:exclamation-thick"></ha-icon></font> '

        tmp_md += (
            " "
            + str(await self.async_relative_time(report["createdTime"])).capitalize()
        )

        tmp_md += "\n\n" + report["text"]

        return tmp_md

    # ------------------------------------------------------
    async def async_formatted_traffic_reports(self) -> None:
        """Format traffic reports."""

        for report in self.traffic_reports:
            report["formated_text"] = await self.async_traffic_report_format(report)
            report["formated_ref_text"] = await self.async_traffic_report_ref_format(
                report
            )
            report["formated_md"] = await self.async_traffic_report_format_md(report)

    # ------------------------------------------------------
    async def async_formatted_important_notices(self) -> None:
        """Format notices."""

        for notice in self.importan_notices:
            notice["formated_text"] = await self.async_important_notice_format(notice)
            notice["formated_md"] = await self.async_important_notice_format_md(notice)

    # ------------------------------------------------------
    async def async_refresh_traffic_reports(self) -> bool:
        """Refresh traffic report."""

        if self.session is None:
            self.session = ClientSession()
            self.close_session = True

        tmp_result: bool = await self.async_get_new_traffic_reports()

        await self.async_formatted_traffic_reports()

        if self.session and self.close_session:
            await self.session.close()

        return tmp_result

    # ------------------------------------------------------
    async def async_refresh_important_notices(self) -> bool:
        """Refresh important notices."""

        if self.session is None:
            self.session = ClientSession()
            self.close_session = True

        tmp_result: bool = await self.async_get_important_notices()
        await self.async_formatted_important_notices()

        if self.session and self.close_session:
            await self.session.close()

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

        if self.max_time_back is None:
            return False

        if (
            dt_util.as_local(datetime.fromisoformat(check_report["createdTime"]))
            < self.max_time_back
        ):
            return True

        return False

    # ------------------------------------------------------
    async def async_get_new_traffic_reports(self, last_post_date: str = "") -> bool:  # noqa: C901
        """Get new traffic report."""

        remove_references: bool = True
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

        traffic_report_url: str = f"https://api.dr.dk/trafik/posts?{region_part_url}{transport_type_part_url}lastPostDate={last_post_date}"

        try:
            async with timeout(self.request_timeout):
                response = await self.session.get(traffic_report_url)
                tmp_json: list = await response.json()

                if len(tmp_json) == 0 or (
                    len(tmp_json) > 0 and await self.async_is_old_report(tmp_json[0])
                ):
                    return False

                first_loop: bool = True

                tmp_report: dict

                for tmp_report in reversed(tmp_json):
                    if first_loop:
                        first_loop = False
                        # Save last post date to use in next request
                        last_post_date: str = tmp_report["createdTime"]

                    id_found: bool = False

                    for report in self.traffic_reports:
                        if report["_id"] == tmp_report["_id"]:
                            id_found = True
                            break

                    if id_found:
                        continue

                    tmp_report["region"] = (
                        str(tmp_report["region"]).lower().replace("-", "_")
                    )
                    tmp_report["type"] = (
                        str(tmp_report["type"]).lower().replace("-", "_")
                    )

                    if await self.async_is_old_report(
                        tmp_report
                    ) is False and await self.async_is_match_traffic_report(tmp_report):
                        self.traffic_reports.insert(0, tmp_report)
                        self.traffic_reports[0]["read"] = False
                        ret_result = True

                if remove_references:
                    for tmp_report in self.traffic_reports:
                        if tmp_report.get("reference") is not None:
                            for ref_report in reversed(self.traffic_reports):
                                if tmp_report["reference"]["_id"] == ref_report["_id"]:
                                    self.traffic_reports.remove(ref_report)
                                    break

                self.traffic_reports.sort(key=lambda x: x["createdTime"], reverse=True)

                if max_row_fetch > 0 and len(self.traffic_reports) > max_row_fetch:
                    done = True

                    for _ in range(len(self.traffic_reports) - max_row_fetch):
                        self.traffic_reports.pop()

        except TimeoutError:
            pass

        if not done:
            if await self.async_get_new_traffic_reports(last_post_date) is True:
                ret_result = True

        # Remove reports older than max_time_back
        if self.entry.options.get(CONF_MAX_TIME_BACK, 0) > 0:
            for report in reversed(self.traffic_reports):
                if await self.async_is_old_report(report):
                    self.traffic_reports.remove(report)
                    ret_result = True

        return ret_result

    # ------------------------------------------------------
    async def async_get_important_notices(self) -> bool:
        """Get important notices."""

        ret_result: bool = False

        important_notices_url: str = "https://api.dr.dk/trafik/notices"

        try:
            async with timeout(self.request_timeout):
                response = await self.session.get(important_notices_url)
                tmp_json: list = await response.json()

                if len(tmp_json) == 0:
                    self.importan_notices.clear()
                    return False

                for tmp_notice in reversed(tmp_json):
                    id_found: bool = False

                    for report in self.importan_notices:
                        if report["_id"] == tmp_notice["_id"]:
                            id_found = True
                            break

                    if id_found:
                        continue

                    self.importan_notices.insert(0, tmp_notice)
                    self.importan_notices[0]["read"] = False
                    ret_result = True

        except TimeoutError:
            pass

        # Remove important notices older than max_time_back
        if self.entry.options.get(CONF_MAX_TIME_BACK, 0) > 0:
            for report in reversed(self.importan_notices):
                if await self.async_is_old_report(report):
                    self.importan_notices.remove(report)
                    ret_result = True

        return ret_result

    # ------------------------------------------------------------------
    def mark_all_traffic_reports_as_read(self) -> None:
        """Mark all traffic reports as read."""

        for report in self.traffic_reports:
            self.mark_traffic_report_as_read(report)

    # ------------------------------------------------------------------
    def mark_traffic_report_as_read(self, report: dict | int) -> None:
        """Mark report as read."""

        if isinstance(report, dict):
            report["read"] = True
        elif isinstance(report, int) and report < len(self.traffic_reports):
            self.traffic_reports[report]["read"] = True

    # ------------------------------------------------------------------
    def mark_current_traffic_report_as_read(self) -> None:
        """Mark report as read."""

        if self.traffic_report_rotate_pos > -1:
            self.traffic_reports[self.traffic_report_rotate_pos]["read"] = True

    # ------------------------------------------------------------------
    def mark_all_important_notices_as_read(self) -> None:
        """Mark all traffic reports as read."""

        for report in self.importan_notices:
            self.mark_important_notice_as_read(report)

    # ------------------------------------------------------------------
    def mark_important_notice_as_read(self, report: dict | int) -> None:
        """Mark report as read."""

        if isinstance(report, dict):
            report["read"] = True
        elif isinstance(report, int) and report < len(self.importan_notices):
            self.importan_notices[report]["read"] = True

    # ------------------------------------------------------------------
    def get_next_traffic_report_pos(self) -> int:
        """Get next traffic report position."""

        if len(self.traffic_reports) == 0 or all(
            value.get("read", False) for value in self.traffic_reports
        ):
            self.traffic_report_rotate_pos = -1

        elif len(self.traffic_reports) == 1:
            self.traffic_report_rotate_pos = 0
        else:
            self.traffic_report_rotate_pos += 1

            if self.traffic_report_rotate_pos > (len(self.traffic_reports) - 1):
                self.traffic_report_rotate_pos = 0

            if self.traffic_reports[self.traffic_report_rotate_pos].get("read", False):
                self.get_next_traffic_report_pos()

        return self.traffic_report_rotate_pos

    # ------------------------------------------------------------------
    def get_prev_traffic_report_pos(self) -> int:
        """Get previous traffic report position."""

        if len(self.traffic_reports) == 0 or all(
            value.get("read", False) for value in self.traffic_reports
        ):
            self.traffic_report_rotate_pos = -1

        elif len(self.traffic_reports) == 1:
            self.traffic_report_rotate_pos = 0
        else:
            self.traffic_report_rotate_pos -= 1

            if self.traffic_report_rotate_pos < 0:
                self.traffic_report_rotate_pos = len(self.traffic_reports) - 1

            if self.traffic_reports[self.traffic_report_rotate_pos].get("read", False):
                self.get_prev_traffic_report_pos()

        return self.traffic_report_rotate_pos
