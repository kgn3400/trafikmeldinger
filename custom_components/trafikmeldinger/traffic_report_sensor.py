"""Traffic reports sensor."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import MATCH_ALL
from homeassistant.core import Event, HomeAssistant, ServiceCall, callback
from homeassistant.helpers import device_registry as dr, issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from . import CommonConfigEntry
from .component_api import ComponentApi
from .const import (
    CONF_LISTEN_TO_TIMER_TRIGGER,
    CONF_MAX_TIME_BACK,
    CONF_RESTART_TIMER,
    CONF_ROTATE_EVERY_MINUTES,
    DICT_REGION,
    DICT_TRANSPORT_TYPE,
    DOMAIN,
    DOMAIN_NAME,
    LOGGER,
    TRANSLATION_KEY,
    TRANSLATION_KEY_MISSING_TIMER_ENTITY,
)
from .entity import ComponentEntity

# from .timer_trigger import TimerTrigger, TimerTriggerErrorEnum
from .hass_util import TimerTrigger, TimerTriggerErrorEnum


# ------------------------------------------------------
# ------------------------------------------------------
class TrafficReportLatestSensor(ComponentEntity, SensorEntity):
    """Sensor class latest traffic report."""

    _unrecorded_attributes = frozenset({MATCH_ALL})

    # ------------------------------------------------------
    def __init__(
        self,
        hass: HomeAssistant,
        entry: CommonConfigEntry,
    ) -> None:
        """Trafikmeldinger sensor."""

        self.hass = hass
        self.entry: CommonConfigEntry = entry

        super().__init__(
            DataUpdateCoordinator(hass, LOGGER, name=DOMAIN, always_update=False),
            entry,
        )
        self.component_api: ComponentApi = entry.runtime_data.component_api

        self.coordinator.update_interval = timedelta(minutes=2)
        # self.coordinator.update_interval = timedelta(seconds=20)
        self.coordinator.update_method = self.async_refresh

        self._name = "Seneste"
        self._unique_id = "seneste"

        self.translation_key = TRANSLATION_KEY

        """Setup the actions for the trafikmelding integration."""
        hass.services.async_register(
            DOMAIN,
            "mark_all_as_read",
            self.async_mark_all_as_read_service,
        )
        hass.services.async_register(
            DOMAIN,
            "unmark_all_as_read",
            self.async_unmark_all_as_read_service,
        )
        hass.services.async_register(
            DOMAIN,
            "mark_all_traffic_reports_as_read",
            self.async_mark_all_traffic_reports_as_read_service,
        )
        hass.services.async_register(
            DOMAIN,
            "unmark_all_traffic_reports_as_read",
            self.async_unmark_all_traffic_reports_as_read_service,
        )
        hass.services.async_register(
            DOMAIN,
            "mark_latest_traffic_report_as_read",
            self.async_mark_latest_traffic_report_as_read_service,
        )
        hass.services.async_register(
            DOMAIN,
            "unmark_latest_traffic_report_as_read",
            self.async_unmark_latest_traffic_report_as_read_service,
        )
        hass.services.async_register(
            DOMAIN,
            "mark_current_traffic_report_as_read",
            self.async_mark_current_traffic_report_as_read_service,
        )
        hass.services.async_register(
            DOMAIN,
            "unmark_current_traffic_report_as_read",
            self.async_unmark_current_traffic_report_as_read_service,
        )

    # ------------------------------------------------------------------
    async def async_mark_all_as_read_service(self, call: ServiceCall) -> None:
        """Mark all as read."""
        await self.hass.services.async_call(
            DOMAIN,
            "mark_all_important_notices_as_read",
        )

        self.component_api.mark_all_traffic_reports_as_read()

        await self.hass.services.async_call(
            DOMAIN,
            "rotate_to_next_traffic_report",
        )
        await self.component_api.storage.async_write_settings()
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------------------
    async def async_unmark_all_as_read_service(self, call: ServiceCall) -> None:
        """Unmark all as read."""
        await self.hass.services.async_call(
            DOMAIN,
            "unmark_all_important_notices_as_read",
        )

        self.component_api.unmark_all_traffic_reports_as_read()

        await self.hass.services.async_call(
            DOMAIN,
            "rotate_to_next_traffic_report",
        )
        await self.component_api.storage.async_write_settings()
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------------------
    async def async_mark_all_traffic_reports_as_read_service(
        self, call: ServiceCall
    ) -> None:
        """Mark all traffic reports as read."""
        self.component_api.mark_all_traffic_reports_as_read()
        await self.component_api.storage.async_write_settings()
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------------------
    async def async_unmark_all_traffic_reports_as_read_service(
        self, call: ServiceCall
    ) -> None:
        """Unmark all traffic reports as read."""
        self.component_api.unmark_all_traffic_reports_as_read()
        await self.component_api.storage.async_write_settings()
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------------------
    async def async_mark_latest_traffic_report_as_read_service(
        self, call: ServiceCall
    ) -> None:
        """Mark latest traffic report as read."""
        self.component_api.mark_traffic_report_as_read(0)
        await self.component_api.storage.async_write_settings()
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------------------
    async def async_unmark_latest_traffic_report_as_read_service(
        self, call: ServiceCall
    ) -> None:
        """Unmark latest traffic report as read."""
        self.component_api.unmark_traffic_report_as_read(0)
        await self.component_api.storage.async_write_settings()
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------------------
    async def async_mark_current_traffic_report_as_read_service(
        self, call: ServiceCall
    ) -> None:
        """Mark latest traffic report as read."""
        self.component_api.mark_current_traffic_report_as_read()
        await self.component_api.storage.async_write_settings()
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------------------
    async def async_unmark_current_traffic_report_as_read_service(
        self, call: ServiceCall
    ) -> None:
        """Unmark latest traffic report as read."""
        self.component_api.unmark_current_traffic_report_as_read()
        await self.component_api.storage.async_write_settings()
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------
    async def async_refresh(self) -> None:
        """Refresh."""
        await self.component_api.async_refresh_traffic_reports()

        self.async_write_ha_state()

    # ------------------------------------------------------
    @property
    def name(self) -> str:
        """Name.

        Returns:
            str: Name

        """
        return self._name

    # ------------------------------------------------------
    @property
    def native_value(self) -> str | None:
        """Native value.

        Returns:
            str | None: Native value

        """

        if len(self.component_api.traffic_reports) == 0 or (
            len(self.component_api.traffic_reports) > 0
            and self.component_api.traffic_reports[0]["read"]
        ):
            return None

        return self.component_api.traffic_reports[0].get("formated_text", "")

    # ------------------------------------------------------
    @property
    def extra_state_attributes(self) -> dict:
        """Extra state attributes.

        Returns:
            dict: Extra state attributes

        """

        attr: dict = {}

        if len(self.component_api.traffic_reports) == 0 or (
            len(self.component_api.traffic_reports) > 0
            and self.component_api.traffic_reports[0]["read"]
        ):
            return attr

        attr["opdateringer"] = self.component_api.traffic_reports[0][
            "formated_updates_text"
        ]
        attr["markdown"] = self.component_api.traffic_reports[0]["formated_md"]
        attr["region"] = DICT_REGION[self.component_api.traffic_reports[0]["region"]]
        attr["transporttype"] = DICT_TRANSPORT_TYPE[
            self.component_api.traffic_reports[0]["type"]
        ]
        attr["oprettet_tidspunkt"] = self.component_api.traffic_reports[0][
            "createdTime"
        ]
        attr["opdateret_tidspunkt"] = self.component_api.traffic_reports[0][
            "updatedTime"
        ]
        attr["afsluttet"] = self.component_api.traffic_reports[0].get(
            "concluded", False
        )
        attr["for_gammel_tidspunkt"] = dt_util.as_local(
            datetime.fromisoformat(self.component_api.traffic_reports[0]["updatedTime"])
            + timedelta(hours=self.entry.options.get(CONF_MAX_TIME_BACK, 0))
        )

        attr["antal_trafikmeldinger"] = len(self.component_api.traffic_reports)
        attr["markeret_som_læst"] = self.component_api.storage.marked_as_read

        return attr

    # ------------------------------------------------------
    @property
    def unique_id(self) -> str:
        """Unique id.

        Returns:
            str: Unique id

        """
        return self._unique_id

    # ------------------------------------------------------
    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    # ------------------------------------------------------
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    # ------------------------------------------------------
    async def async_update(self) -> None:
        """Update the entity. Only used by the generic entity update service."""
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""

        await self.async_refresh()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

        self.hass.bus.async_listen(
            dr.EVENT_DEVICE_REGISTRY_UPDATED,
            self._handle_device_registry_updated,
        )

    # ------------------------------------------------------
    @callback
    async def _handle_device_registry_updated(
        self, event: Event[dr.EventDeviceRegistryUpdatedData]
    ) -> None:
        """Handle when device registry updated."""

        if event.data["action"] == "remove":
            await self.component_api.storage.async_remove_settings()


# ------------------------------------------------------
# ------------------------------------------------------
class TrafficReportRotateSensor(ComponentEntity, SensorEntity):
    """Sensor class latest traffic report."""

    _unrecorded_attributes = frozenset({MATCH_ALL})

    # ------------------------------------------------------
    def __init__(
        self,
        hass: HomeAssistant,
        entry: CommonConfigEntry,
    ) -> None:
        """Trafikmeldinger sensor."""

        self.hass: HomeAssistant = hass
        self.entry: CommonConfigEntry = entry

        super().__init__(
            DataUpdateCoordinator(
                hass,
                LOGGER,
                name=DOMAIN,
            ),
            entry,
        )
        self.coordinator.update_method = self.async_refresh_dummy

        self.component_api: ComponentApi = entry.runtime_data.component_api

        self._name = "Roterende"
        self._unique_id = "roterende"

        self.translation_key = TRANSLATION_KEY

        self.timer_trigger = TimerTrigger(
            self,
            timer_entity=entry.options.get(CONF_LISTEN_TO_TIMER_TRIGGER, ""),
            duration=timedelta(
                minutes=entry.options.get(CONF_ROTATE_EVERY_MINUTES, 0.5)
            ),
            callback_trigger=self.async_refresh,
            auto_restart=entry.options.get(CONF_RESTART_TIMER, False),
        )

        hass.services.async_register(
            DOMAIN,
            "rotate_to_next_traffic_report",
            self.async_rotate_to_next_traffic_report_service,
        )

    # ------------------------------------------------------------------
    async def async_rotate_to_next_traffic_report_service(
        self, call: ServiceCall
    ) -> None:
        """Mark all as read."""
        self.component_api.get_next_traffic_report_pos()
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------
    async def async_refresh_dummy(self) -> None:
        """Refresh."""
        await self.async_refresh(False)

    # ------------------------------------------------------
    async def async_refresh(self, error: TimerTriggerErrorEnum) -> None:
        """Refresh."""

        if error:
            match error:
                case TimerTriggerErrorEnum.MISSING_TIMER_ENTITY:
                    ir.async_create_issue(
                        self.hass,
                        DOMAIN,
                        DOMAIN_NAME + datetime.now().isoformat(),
                        issue_domain=DOMAIN,
                        is_fixable=False,
                        severity=ir.IssueSeverity.WARNING,
                        translation_key=TRANSLATION_KEY_MISSING_TIMER_ENTITY,
                        translation_placeholders={
                            "timer_entity": self.entry.options.get(
                                CONF_LISTEN_TO_TIMER_TRIGGER, ""
                            ),
                            "entity": self.entity_id,
                        },
                    )
                case _:
                    pass
            return

        self.component_api.get_next_traffic_report_pos()
        self.async_write_ha_state()

    # ------------------------------------------------------
    @property
    def name(self) -> str:
        """Name.

        Returns:
            str: Name

        """
        return self._name

    # ------------------------------------------------------
    @property
    def native_value(self) -> str | None:
        """Native value.

        Returns:
            str | None: Native value

        """

        if (
            self.component_api.traffic_report_rotate_pos == -1
            or len(self.component_api.traffic_reports) == 0
        ):
            return None

        return self.component_api.traffic_reports[
            self.component_api.traffic_report_rotate_pos
        ].get("formated_text", "")

    # ------------------------------------------------------
    @property
    def extra_state_attributes(self) -> dict:
        """Extra state attributes.

        Returns:
            dict: Extra state attributes

        """

        attr: dict = {}

        if (
            self.component_api.traffic_report_rotate_pos == -1
            or len(self.component_api.traffic_reports) == 0
        ):
            return attr

        attr["opdateringer"] = self.component_api.traffic_reports[
            self.component_api.traffic_report_rotate_pos
        ]["formated_updates_text"]

        attr["markdown"] = self.component_api.traffic_reports[
            self.component_api.traffic_report_rotate_pos
        ]["formated_md"]
        attr["region"] = DICT_REGION[
            self.component_api.traffic_reports[
                self.component_api.traffic_report_rotate_pos
            ]["region"]
        ]
        attr["transporttype"] = DICT_TRANSPORT_TYPE[
            self.component_api.traffic_reports[
                self.component_api.traffic_report_rotate_pos
            ]["type"]
        ]
        attr["oprettet_tidspunkt"] = self.component_api.traffic_reports[
            self.component_api.traffic_report_rotate_pos
        ]["createdTime"]
        attr["opdateret_tidspunkt"] = self.component_api.traffic_reports[
            self.component_api.traffic_report_rotate_pos
        ]["updatedTime"]

        attr["antal_trafikmeldinger"] = len(self.component_api.traffic_reports)
        attr["markeret_som_læst"] = self.component_api.storage.marked_as_read

        return attr

    # ------------------------------------------------------
    @property
    def unique_id(self) -> str:
        """Unique id.

        Returns:
            str: Unique id

        """
        return self._unique_id

    # ------------------------------------------------------
    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    # ------------------------------------------------------
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    # ------------------------------------------------------
    async def async_update(self) -> None:
        """Update the entity. Only used by the generic entity update service."""
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await self.async_refresh(False)
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
