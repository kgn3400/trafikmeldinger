"""Constants for Trafikmeldinger integration."""

from logging import Logger, getLogger

DOMAIN = "trafikmeldinger"
DOMAIN_NAME = "Trafikmeldinger"
LOGGER: Logger = getLogger(__name__)

TRANSLATION_KEY = DOMAIN
TRANSLATE_EXTRA = "options.step.extra.data"

CONF_REGION = "region"
CONF_REGION_ALL = "ALL"
CONF_REGION_CPH = "CPH"
CONF_REGION_MID_NORTH = "MID-NORTH"
CONF_REGION_SOUTH = "SOUTH"
TRANSLATION_KEY_REGION = CONF_REGION
TEXT_REGION_CPH = "København og Sjælland"
TEXT_REGION_MID_NORTH = "Midt-, Nord- og Østjylland"
TEXT_REGION_SOUTH = "Fyn, Trekanten og Sydjylland"

CONF_TRANSPORT_TYPE = "transport_type"
CONF_TRANSPORT_TYPE_ALL = "ALL"
CONF_TRANSPORT_TYPE_PUBLIC = "PUBLIC"
CONF_TRANSPORT_TYPE_PRIVATE = "PRIVATE"
TRANSLATION_KEY_TRANSPORT_TYPE = CONF_TRANSPORT_TYPE

CONF_MAX_TIME_BACK = "max_time_back"
CONF_MAX_ROW_FETCH = "max_row_fetch"

CONF_SCROLL_MESSAGES_EVERY_MINUTES: str = "scroll_messages_every_minutes"
CONF_RESTART_TIMER = "restart_timer"
CONF_LISTEN_TO_TIMER_TRIGGER = "listen_to_timer_trigger"
