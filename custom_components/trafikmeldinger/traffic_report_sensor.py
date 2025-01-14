"""Traffic reports sensor."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import CommonConfigEntry
from .component_api import ComponentApi
from .const import (
    CONF_LISTEN_TO_TIMER_TRIGGER,
    CONF_RESTART_TIMER,
    DICT_REGION,
    DICT_TRANSPORT_TYPE,
    DOMAIN,
    LOGGER,
    TRANSLATION_KEY,
)
from .entity import ComponentEntity
from .timer_trigger import TimerTrigger


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
        # self.coordinator: DataUpdateCoordinator = DataUpdateCoordinator(
        #     hass,
        #     LOGGER,
        #     name=DOMAIN,
        #     update_interval=timedelta(minutes=1),
        #     update_method=self.async_refresh,
        # )
        self.hass = hass
        self.entry: CommonConfigEntry = entry

        super().__init__(
            DataUpdateCoordinator(
                hass,
                LOGGER,
                name=DOMAIN,
                # update_interval=timedelta(minutes=1),
                # update_method=self.async_refresh,
            ),
            entry,
        )
        self.component_api: ComponentApi = entry.runtime_data.component_api

        self.coordinator.update_interval = timedelta(minutes=1)
        self.coordinator.update_method = self.async_refresh

        self._name = "Seneste"
        self._unique_id = "seneste"

        self.translation_key = TRANSLATION_KEY

    # ------------------------------------------------------
    async def async_refresh(self) -> None:
        """Refresh."""
        if await self.component_api.async_refresh_traffic_reports():
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

        if len(self.component_api.traffic_reports) == 0:
            return None
        return self.component_api.traffic_reports[0]["formated_text"]

    # ------------------------------------------------------
    @property
    def extra_state_attributes(self) -> dict:
        """Extra state attributes.

        Returns:
            dict: Extra state attributes

        """

        attr: dict = {}

        if len(self.component_api.traffic_reports) == 0:
            return attr
        attr["trafikmelding_md"] = self.component_api.traffic_reports[0]["formated_md"]
        attr["region"] = DICT_REGION[self.component_api.traffic_reports[0]["region"]]
        attr["transport_type"] = DICT_TRANSPORT_TYPE[
            self.component_api.traffic_reports[0]["type"]
        ]
        attr["oprettet_tidspunkt"] = self.component_api.traffic_reports[0][
            "createdTime"
        ]

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
        # self.coordinator: DataUpdateCoordinator = DataUpdateCoordinator(
        #     hass,
        #     LOGGER,
        #     name=DOMAIN,
        # )

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

        self._name = "Meldinger"
        self._unique_id = "meldinger"

        self.translation_key = TRANSLATION_KEY

        if entry.options.get(CONF_LISTEN_TO_TIMER_TRIGGER, ""):
            self.timer_trigger = TimerTrigger(
                self,
                entry.options.get(CONF_LISTEN_TO_TIMER_TRIGGER, ""),
                self.async_refresh,
                entry.options.get(CONF_RESTART_TIMER, False),
            )

    # ------------------------------------------------------
    async def async_refresh_dummy(self) -> None:
        """Refresh."""
        await self.async_refresh(False)

    # ------------------------------------------------------
    async def async_refresh(self, error: bool) -> None:
        """Refresh."""
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

        if self.component_api.traffic_report_rotate_pos == -1:
            return None

        return self.component_api.traffic_reports[
            self.component_api.traffic_report_rotate_pos
        ]["formated_text"]

    # ------------------------------------------------------
    @property
    def extra_state_attributes(self) -> dict:
        """Extra state attributes.

        Returns:
            dict: Extra state attributes

        """

        attr: dict = {}

        if self.component_api.traffic_report_rotate_pos == -1:
            return attr
        attr["trafikmelding_md"] = self.component_api.traffic_reports[
            self.component_api.traffic_report_rotate_pos
        ]["formated_md"]
        attr["region"] = DICT_REGION[
            self.component_api.traffic_reports[
                self.component_api.traffic_report_rotate_pos
            ]["region"]
        ]
        attr["transport_type"] = DICT_TRANSPORT_TYPE[
            self.component_api.traffic_reports[
                self.component_api.traffic_report_rotate_pos
            ]["type"]
        ]
        attr["oprettet_tidspunkt"] = self.component_api.traffic_reports[
            self.component_api.traffic_report_rotate_pos
        ]["createdTime"]

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
