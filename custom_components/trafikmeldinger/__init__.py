"""The Trafikmeldinger integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .component_api import ComponentApi

PLATFORMS: list[Platform] = [Platform.SENSOR]


# ------------------------------------------------------------------
# ------------------------------------------------------------------
@dataclass
class CommonData:
    """Common data."""

    component_api: ComponentApi


# The type alias needs to be suffixed with 'ConfigEntry'
type CommonConfigEntry = ConfigEntry[CommonData]


# ------------------------------------------------------------------
async def async_setup_entry(hass: HomeAssistant, entry: CommonConfigEntry) -> bool:
    """Set up Trafikmeldinger from a config entry."""

    component_api: ComponentApi = ComponentApi(
        hass,
        entry,
        async_get_clientsession(hass),
    )

    await component_api.storage.async_read_settings()

    entry.async_on_unload(entry.add_update_listener(config_update_listener))
    entry.runtime_data = CommonData(
        component_api=component_api,
        # coordinator=coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # await coordinator.async_config_entry_first_refresh()

    return True


# ------------------------------------------------------------------
async def async_unload_entry(hass: HomeAssistant, entry: CommonConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


# ------------------------------------------------------------------
async def async_reload_entry(hass: HomeAssistant, entry: CommonConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


# ------------------------------------------------------------------
async def config_update_listener(
    hass: HomeAssistant,
    config_entry: CommonConfigEntry,
) -> None:
    """Reload on config entry update."""

    await hass.config_entries.async_reload(config_entry.entry_id)
