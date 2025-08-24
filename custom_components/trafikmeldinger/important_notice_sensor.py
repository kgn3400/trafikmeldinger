"""Important notice sensor."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import CommonConfigEntry
from .component_api import ComponentApi
from .const import DOMAIN, LOGGER, TRANSLATION_KEY
from .entity import ComponentEntity


# ------------------------------------------------------
# ------------------------------------------------------
class ImportantNoticeLatestSensor(ComponentEntity, SensorEntity):
    """Sensor class Important notice."""

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
                update_interval=timedelta(minutes=4),
                update_method=self.async_refresh,
                config_entry=entry,
            ),
            entry,
        )

        self.component_api: ComponentApi = entry.runtime_data.component_api

        self.coordinator.update_interval = timedelta(minutes=5)
        self.coordinator.update_method = self.async_refresh

        self._name = "Vigtig besked"
        self._unique_id = "vigtig_besked"

        self.translation_key = TRANSLATION_KEY

        """Setup the actions for the trafikmelding integration."""
        hass.services.async_register(
            DOMAIN,
            "mark_all_important_notices_as_read",
            self.async_mark_all_important_notices_as_read_service,
        )
        hass.services.async_register(
            DOMAIN,
            "unmark_all_important_notices_as_read",
            self.async_unmark_all_important_notices_as_read_service,
        )

    # ------------------------------------------------------------------
    async def async_mark_all_important_notices_as_read_service(
        self, call: ServiceCall
    ) -> None:
        """Mark all important notices as read."""
        self.component_api.mark_all_important_notices_as_read()
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------------------
    async def async_unmark_all_important_notices_as_read_service(
        self, call: ServiceCall
    ) -> None:
        """Unmark all important notices as read."""
        self.component_api.unmark_all_important_notices_as_read()
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------
    async def async_refresh(self) -> None:
        """Refresh."""
        await self.component_api.async_refresh_important_notices()

        await self.component_api.async_important_notice_event_fire()

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

        if len(self.component_api.important_notices) == 0 or (
            len(self.component_api.important_notices) > 0
            and self.component_api.important_notices[0]["read"]
        ):
            return None

        return self.component_api.important_notices[0]["formated_text"]

    # ------------------------------------------------------
    @property
    def extra_state_attributes(self) -> dict:
        """Extra state attributes.

        Returns:
            dict: Extra state attributes

        """

        attr: dict = {}

        if len(self.component_api.important_notices) == 0 or (
            len(self.component_api.important_notices) > 0
            and self.component_api.important_notices[0]["read"]
        ):
            return attr

        attr["markdown"] = self.component_api.important_notices[0]["markdown"]
        attr["oprettet_tidspunkt"] = self.component_api.important_notices[0][
            "createdTime"
        ]
        attr["opdateret_tidspunkt"] = self.component_api.important_notices[0][
            "updatedTime"
        ]
        attr["antal_vigtige_beskeder"] = len(self.component_api.important_notices)

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
