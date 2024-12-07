"""Component api for Trafikmeldinger."""

from asyncio import timeout
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import partial

from aiohttp.client import ClientSession
from babel.dates import format_timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_MAX_ROW_FETCH,
    CONF_MAX_TIME_BACK,
    CONF_REGION,
    CONF_REGION_ALL,
    CONF_REGION_CPH,
    CONF_REGION_MID_NORTH,
    CONF_REGION_SOUTH,
    CONF_TRANSPORT_TYPE,
    CONF_TRANSPORT_TYPE_ALL,
    CONF_TRANSPORT_TYPE_PRIVATE,
    CONF_TRANSPORT_TYPE_PUBLIC,
    TEXT_REGION_CPH,
    TEXT_REGION_MID_NORTH,
    TEXT_REGION_SOUTH,
    TRANSLATE_EXTRA,
)
from .translate import Translate


# ------------------------------------------------------------------
# ------------------------------------------------------------------
@dataclass
class Translations:
    """Translations."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Init."""

        self.now_str: str
        self.for_str: str

        self.ago_str: str

        self.message_str: str
        self.messages_str: str

        self.last_message_str: str

        self.received_str: str
        self.relevance_str: str

        self.all_str: str
        self.info_str: str
        self.attention_str: str
        self.warning_str: str
        self.error_str: str

        self.translate: Translate = Translate(hass, TRANSLATE_EXTRA)

    # ------------------------------------------------------------------
    async def async_refresh(self):
        """Refresh."""
        self.now_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".rt_now",
        )

        self.for_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".rt_for",
        )

        self.ago_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".rt_ago",
        )

        self.received_str = await self.translate.async_get_localized_str(
            TRANSLATE_EXTRA + ".received",
        )


# ------------------------------------------------------------------
# ------------------------------------------------------------------
@dataclass
class ComponentApi:
    """Trafikmeldinger interface."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        session: ClientSession | None,
    ) -> None:
        """Trafikmeldinger api."""

        self.hass: HomeAssistant = hass
        self.coordinator: DataUpdateCoordinator = coordinator
        self.entry: ConfigEntry = entry
        self.session: ClientSession | None = session

        self.supress_update_listener: bool = False

        self.close_session: bool = False

        self.request_timeout: int = 10
        self.trafiq_report: list = []

        # self.translations: Translations = Translations(hass)

    # ------------------------------------------------------------------
    async def async_init(self) -> None:
        """Async init."""
        await self.translations.async_refresh()

    # ------------------------------------------------------------------
    async def async_relative_time_received(self, date_time: datetime) -> str:
        """Relative time received."""

        return (
            self.translations.received_str
            + " "
            + await self.async_relative_time(date_time)
        )

    # ------------------------------------------------------------------
    async def async_relative_time(self, iso_datetime: str) -> str:
        """Relative time."""

        now = datetime.now(UTC)
        diff: timedelta = dt_util.as_local(datetime.fromisoformat(iso_datetime)) - now

        diff_str: str = await self.hass.async_add_executor_job(
            partial(
                format_timedelta,
                delta=diff,
                add_direction=True,
                locale="da",
                # locale=self.translations.translate.acive_language,
            )
        )
        return diff_str

    # ------------------------------------------------------
    async def async_trafic_report_format(self, report_number: int) -> str:
        """Trafic report format."""

        if report_number < len(self.trafiq_report):
            return self.trafiq_report[report_number]["text"][:255]

        return ""

    # ------------------------------------------------------
    async def async_trafic_report_format_md(self, report_number: int) -> str:
        """Trafic report format markdown."""

        tmp_md: str = ""

        if report_number < len(self.trafiq_report):
            if self.trafiq_report[report_number]["type"] == CONF_TRANSPORT_TYPE_PRIVATE:
                tmp_md = (
                    '###  <font color=red> <ha-icon icon="mdi:car"></ha-icon></font> '
                )
            else:
                tmp_md = '###  <font color=red> <ha-icon icon="mdi:train-bus"></ha-icon></font> '

            if self.trafiq_report[report_number]["region"] == CONF_REGION_CPH:
                tmp_md += TEXT_REGION_CPH
            elif self.trafiq_report[report_number]["region"] == CONF_REGION_MID_NORTH:
                tmp_md += TEXT_REGION_MID_NORTH
            elif self.trafiq_report[report_number]["region"] == CONF_REGION_SOUTH:
                tmp_md += TEXT_REGION_SOUTH

            tmp_md += " " + await self.async_relative_time(
                self.trafiq_report[report_number]["createdTime"]
            )

            tmp_md += "\n\n" + self.trafiq_report[report_number]["text"]

            if self.trafiq_report[report_number].get("reference", None) is not None:
                tmp_md += (
                    "\n\n>" + self.trafiq_report[report_number]["reference"]["text"]
                )

        return tmp_md

    # ------------------------------------------------------
    async def async_formatted_trafic_reports(self) -> None:
        """Refresh trafic report."""

        for x, report in enumerate(self.trafiq_report):
            report["formated_text"] = await self.async_trafic_report_format(x)
            report["formated_md"] = await self.async_trafic_report_format_md(x)

    # ------------------------------------------------------
    async def async_refresh_trafic_reports(self) -> bool:
        """Refresh trafic report."""

        # Remove reports older than max_time_back
        if self.entry.options.get(CONF_MAX_TIME_BACK, 0) > 0:
            max_time_back: datetime = dt_util.now() - datetime.timedelta(
                hours=self.entry.options[CONF_MAX_TIME_BACK]
            )

            for report in reversed(self.trafiq_report):
                if report["createdTime"] < max_time_back.isoformat():
                    self.trafiq_report.remove(report)

        if self.session is None:
            self.session = ClientSession()
            self.close_session = True

        tmp_result: bool = await self.async_get_new_trafic_reports()

        if self.session and self.close_session:
            await self.session.close()

        await self.async_formatted_trafic_reports()
        return tmp_result

    # ------------------------------------------------------
    async def async_get_new_trafic_reports(self, last_post_date: str = "") -> bool:
        """Get new trafic report."""
        trafiq_report_url: str = (
            f"https://api.dr.dk/trafik/posts?lastPostDate={last_post_date}"
        )

        remove_references: bool = True
        done: bool = False
        ret_result: bool = False

        max_time_back: datetime | None = None

        if self.entry.options.get(CONF_MAX_TIME_BACK, 0) > 0:
            max_time_back = dt_util.now() - datetime.timedelta(
                hours=self.entry.options[CONF_MAX_TIME_BACK]
            )

        max_row_fetch: int = self.entry.options.get(CONF_MAX_ROW_FETCH, 0)

        if max_row_fetch == 0:
            max_row_fetch = 40

        region: list = self.entry.options.get(CONF_REGION, [CONF_REGION_ALL])

        if len(region) == 0 or (len(region) == 1 and region[0] == CONF_REGION_ALL):
            region: list = [CONF_REGION_CPH, CONF_REGION_MID_NORTH, CONF_REGION_SOUTH]

        transport_type: list = self.entry.options.get(
            CONF_TRANSPORT_TYPE, [CONF_TRANSPORT_TYPE_ALL]
        )

        if len(transport_type) == 0 or (
            len(transport_type) == 1 and transport_type[0] == CONF_TRANSPORT_TYPE_ALL
        ):
            transport_type: list = [
                CONF_TRANSPORT_TYPE_PRIVATE,
                CONF_TRANSPORT_TYPE_PUBLIC,
            ]

        try:
            async with timeout(self.request_timeout):
                response = await self.session.get(trafiq_report_url)
                tmp_json: list = await response.json()

                if len(tmp_json) == 0:
                    done = True

                first_loop: bool = True

                for tmp_report in reversed(tmp_json):
                    if first_loop:
                        first_loop = False
                        last_post_date: str = tmp_report["createdTime"]

                    for report in self.trafiq_report:
                        if report["_id"] == tmp_report["_id"]:
                            done = True
                            break

                    if done:
                        break

                    if (
                        tmp_report["region"] in region
                        and tmp_report["type"] in transport_type
                    ):
                        if (
                            max_time_back is not None
                            and (
                                dt_util.as_local(
                                    datetime.fromisoformat(tmp_report["createdTime"])
                                )
                            )
                            < max_time_back
                        ):
                            self.trafiq_report.insert(0, tmp_report)
                            ret_result = True
                        else:
                            self.trafiq_report.insert(0, tmp_report)
                            ret_result = True

                        if remove_references:
                            if tmp_report.get("reference", None) is not None:
                                for ref_report in reversed(self.trafiq_report):
                                    if (
                                        tmp_report["reference"]["_id"]
                                        == ref_report["_id"]
                                    ):
                                        self.trafiq_report.remove(ref_report)
                                        break

                self.trafiq_report.sort(key=lambda x: x["createdTime"], reverse=True)

                if max_row_fetch > 0 and len(self.trafiq_report) > max_row_fetch:
                    done = True

                    for _ in range(len(self.trafiq_report) - max_row_fetch):
                        self.trafiq_report.pop()

        except TimeoutError:
            pass

        if not done:
            if await self.async_get_new_trafic_reports(last_post_date) is True:
                ret_result = True

        return ret_result

    # ------------------------------------------------------------------
    async def update_config(self) -> None:
        """Update config."""

        # tmp_options: dict[str, Any] = self.entry.options.copy()
        # tmp_options[CONF_MSG] = self.msg
        # tmp_options[CONF_CONTENT] = self.content
        # tmp_options[CONF_IS_ON] = self.is_on
        # self.supress_update_listener = True

        # self.hass.config_entries.async_update_entry(
        #     self.entry, data=tmp_options, options=tmp_options
        # )
