"""Constants for Trafikmeldinger integration."""

from logging import Logger, getLogger

DOMAIN = "trafikmeldinger"
DOMAIN_NAME = "Trafikmeldinger"
LOGGER: Logger = getLogger(__name__)

TRANSLATION_KEY = DOMAIN
TRANSLATION_KEY_MISSING_TIMER_ENTITY = "missing_timer_entity"

CONF_REGION = "region"
CONF_REGION_ALL = "all"
CONF_REGION_CPH = "cph"
CONF_REGION_MID_NORTH = "mid_north"
CONF_REGION_SOUTH = "south"
TRANSLATION_KEY_REGION = CONF_REGION
TEXT_REGION_ALL = "Hele landet"
TEXT_REGION_CPH = "København og Sjælland"
TEXT_REGION_MID_NORTH = "Midt-, Nord- og Østjylland"
TEXT_REGION_SOUTH = "Fyn, Trekanten og Sydjylland"
DICT_REGION = {
    CONF_REGION_ALL: TEXT_REGION_ALL,
    CONF_REGION_CPH: TEXT_REGION_CPH,
    CONF_REGION_MID_NORTH: TEXT_REGION_MID_NORTH,
    CONF_REGION_SOUTH: TEXT_REGION_SOUTH,
}

CONF_TRANSPORT_TYPE = "transport_type"
CONF_TRANSPORT_TYPE_ALL = "all"
CONF_TRANSPORT_TYPE_PUBLIC = "public"
CONF_TRANSPORT_TYPE_PRIVATE = "private"
TRANSLATION_KEY_TRANSPORT_TYPE = CONF_TRANSPORT_TYPE
TEXT_TRANSPORT_TYPE_ALL = "Alle transport typer"
TEXT_TRANSPORT_TYPE_PUBLIC = "kollektiv transport"
TEXT_TRANSPORT_TYPE_PRIVATE = "Biltrafik"
DICT_TRANSPORT_TYPE = {
    CONF_TRANSPORT_TYPE_ALL: TEXT_TRANSPORT_TYPE_ALL,
    CONF_TRANSPORT_TYPE_PUBLIC: TEXT_TRANSPORT_TYPE_PUBLIC,
    CONF_TRANSPORT_TYPE_PRIVATE: TEXT_TRANSPORT_TYPE_PRIVATE,
}

CONF_MAX_TIME_BACK = "max_time_back"
CONF_MAX_TIME_BACK_CONCLUDED = "max_time_back_concluded"
CONF_MAX_ROW_FETCH = "max_row_fetch"
CONF_ONLY_SHOW_LAST_UPDATE = "only_show_last_update"
CONF_RESTART_TIMER = "restart_timer"
CONF_LISTEN_TO_TIMER_TRIGGER = "listen_to_timer_trigger"
CONF_ROTATE_EVERY_MINUTES = "rotate_every_minutes"

CONF_INCL_LATEST_IN_PREVIOUS_TRAFFIC_REPORTS = "incl_latest_in_previous_traffic_reports"

CONF_SUM_INCL_IMPORTANT_NOTICES = "sum_incl_important_notices"
CONF_SUM_INCL_LATEST_TRAFFIC_REPORT = "sum_incl_latest_traffic_report"
CONF_SUM_INCL_PREVIOUS_TRAFFIC_REPORTS = "sum_incl_previous_traffic_reports"

CONF_MATCH = "match"
CONF_MATCH_CASE = "match_case"
CONF_MATCH_WORD = "match_word"
CONF_MATCH_LIST = "match_list"

STORAGE_VERSION = 1
STORAGE_KEY = DOMAIN

EVENT_NEW_TRAFFIC_REPORT = "new_traffic_report"
EVENT_NEW_IMPORTANT_NOTICE = "new_important_notice"
