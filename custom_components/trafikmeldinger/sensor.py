"""Trafikmeldinger sensor."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CommonConfigEntry
from .component_api import ComponentApi
from .const import TRANSLATION_KEY
from .entity import ComponentEntity


# ------------------------------------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    entry: CommonConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Entry for Trafikmeldinger setup."""

    sensors = []

    sensors.append(TraficReportSensor(entry))

    async_add_entities(sensors)


# ------------------------------------------------------
# ------------------------------------------------------
class TraficReportSensor(ComponentEntity, SensorEntity):
    """Sensor class Trafikmeldinger."""

    # ------------------------------------------------------
    def __init__(
        self,
        entry: CommonConfigEntry,
    ) -> None:
        """Trafikmeldinger sensor."""
        super().__init__(entry.runtime_data.coordinator, entry)

        self.component_api: ComponentApi = entry.runtime_data.component_api

        self.coordinator.update_interval = timedelta(minutes=1)
        self.coordinator.update_method = self.async_refresh

        self._name = "Message"
        self._unique_id = "message"

        self.translation_key = TRANSLATION_KEY

    # ------------------------------------------------------
    async def async_refresh(self) -> None:
        """Refresh."""
        if await self.component_api.async_refresh_trafic_reports():
            self.async_write_ha_state()

    # ------------------------------------------------------
    @property
    def name(self) -> str:
        """Name.

        Returns:
            str: Name

        """
        return self._name

    @property
    def native_value(self) -> str | None:
        """Native value.

        Returns:
            str | None: Native value

        """

        if len(self.component_api.trafiq_report) == 0:
            return None
        return self.component_api.trafiq_report[0]["formated_text"]

    # ------------------------------------------------------
    @property
    def extra_state_attributes(self) -> dict:
        """Extra state attributes.

        Returns:
            dict: Extra state attributes

        """

        attr: dict = {}

        if len(self.component_api.trafiq_report) == 0:
            return attr
        attr["report_md"] = self.component_api.trafiq_report[0]["formated_md"]

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
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
        await self.component_api.async_init()