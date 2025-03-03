"""Trafikmeldinger sensor."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CommonConfigEntry
from .important_notice_sensor import ImportantNoticeLatestSensor
from .traffic_report_sensor import TrafficReportLatestSensor, TrafficReportRotateSensor


# ------------------------------------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    entry: CommonConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Entry for Trafikmeldinger setup."""

    sensors: list = [
        ImportantNoticeLatestSensor(hass, entry),
        TrafficReportLatestSensor(hass, entry),
    ]

    sensors.append(TrafficReportRotateSensor(hass, entry))

    async_add_entities(sensors)
