"""Config flow for trafikmeldinger integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

import voluptuous as vol

from homeassistant.helpers.schema_config_entry_flow import (
    SchemaCommonFlowHandler,
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
)
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
)

# from homeassistant.data_entry_flow import section
#  from homeassistant import config_entries
from .const import (
    CONF_INCL_LATEST_IN_PREVIOUS_TRAFFIC_REPORTS,
    CONF_LISTEN_TO_TIMER_TRIGGER,
    CONF_MATCH_CASE,
    CONF_MATCH_LIST,
    CONF_MATCH_WORD,
    CONF_MAX_ROW_FETCH,
    CONF_MAX_TIME_BACK,
    CONF_MAX_TIME_BACK_CONCLUDED,
    CONF_ONLY_SHOW_LAST_UPDATE,
    CONF_OVERVIEW_IMPORTANT_NOTICES,
    CONF_OVERVIEW_LATEST_TRAFFIC_REPORT,
    CONF_OVERVIEW_PREVIOUS_TRAFFIC_REPORTS,
    CONF_REGION,
    CONF_REGION_ALL,
    CONF_REGION_CPH,
    CONF_REGION_MID_NORTH,
    CONF_REGION_SOUTH,
    CONF_RESTART_TIMER,
    CONF_ROTATE_EVERY_MINUTES,
    CONF_TRANSPORT_TYPE,
    CONF_TRANSPORT_TYPE_ALL,
    CONF_TRANSPORT_TYPE_PRIVATE,
    CONF_TRANSPORT_TYPE_PUBLIC,
    DOMAIN,
    DOMAIN_NAME,
    TRANSLATION_KEY_REGION,
    TRANSLATION_KEY_TRANSPORT_TYPE,
)


# ------------------------------------------------------------------
async def _validate_input(
    handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
) -> dict[str, Any]:
    """Validate the user input."""

    # if (
    #     user_input[CONF_GENERAL_MSG] is False
    #     and user_input[CONF_CITY_CHECK] is False
    #     and user_input[CONF_STREET_CHECK] is False
    # ):
    #     raise SchemaFlowError("missing_selection")

    return user_input


CONFIG_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_REGION, default=[CONF_REGION_ALL]): SelectSelector(
            SelectSelectorConfig(
                multiple=True,
                options=[
                    CONF_REGION_ALL,
                    CONF_REGION_CPH,
                    CONF_REGION_MID_NORTH,
                    CONF_REGION_SOUTH,
                ],
                sort=True,
                mode=SelectSelectorMode.DROPDOWN,
                translation_key=TRANSLATION_KEY_REGION,
            )
        ),
        vol.Required(
            CONF_TRANSPORT_TYPE, default=[CONF_TRANSPORT_TYPE_ALL]
        ): SelectSelector(
            SelectSelectorConfig(
                multiple=True,
                options=[
                    CONF_TRANSPORT_TYPE_ALL,
                    CONF_TRANSPORT_TYPE_PUBLIC,
                    CONF_TRANSPORT_TYPE_PRIVATE,
                ],
                sort=True,
                mode=SelectSelectorMode.DROPDOWN,
                translation_key=TRANSLATION_KEY_TRANSPORT_TYPE,
            )
        ),
        vol.Required(
            CONF_MAX_TIME_BACK,
            default=12,
        ): NumberSelector(
            NumberSelectorConfig(
                min=0,
                max=48,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement="timer",
            )
        ),
        vol.Required(
            CONF_MAX_TIME_BACK_CONCLUDED,
            default=2,
        ): NumberSelector(
            NumberSelectorConfig(
                min=0,
                max=48,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement="timer",
            )
        ),
        vol.Required(
            CONF_MAX_ROW_FETCH,
            default=20,
        ): NumberSelector(
            NumberSelectorConfig(
                min=0,
                max=48,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement="rækker",
            )
        ),
        vol.Required(
            CONF_ROTATE_EVERY_MINUTES,
            default=0.50,
        ): NumberSelector(
            NumberSelectorConfig(
                min=0.25,
                max=999,
                step=0.25,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement="minutter",
            )
        ),
        vol.Optional(
            CONF_LISTEN_TO_TIMER_TRIGGER,
        ): EntitySelector(
            EntitySelectorConfig(integration="timer", multiple=False),
        ),
        vol.Optional(
            CONF_RESTART_TIMER,
            default=True,
        ): BooleanSelector(),
    }
)

CONFIG_OPTIONS_SCHEMA_MATCH = vol.Schema(
    {
        vol.Optional(CONF_MATCH_LIST, default=[]): TextSelector(
            TextSelectorConfig(multiple=True)
        ),
        vol.Optional(CONF_MATCH_CASE, default=False): BooleanSelector(),
        vol.Optional(CONF_MATCH_WORD, default=False): BooleanSelector(),
    }
)

CONFIG_OPTIONS_SCHEMA_EXTRA = vol.Schema(
    {
        vol.Optional(
            CONF_ONLY_SHOW_LAST_UPDATE,
            default=True,
        ): BooleanSelector(),
        vol.Optional(
            CONF_INCL_LATEST_IN_PREVIOUS_TRAFFIC_REPORTS, default=False
        ): BooleanSelector(),
        vol.Optional(CONF_OVERVIEW_IMPORTANT_NOTICES, default=True): BooleanSelector(),
        vol.Optional(
            CONF_OVERVIEW_LATEST_TRAFFIC_REPORT, default=True
        ): BooleanSelector(),
        vol.Optional(
            CONF_OVERVIEW_PREVIOUS_TRAFFIC_REPORTS, default=True
        ): BooleanSelector(),
    }
)

CONFIG_FLOW = {
    "user": SchemaFlowFormStep(
        CONFIG_OPTIONS_SCHEMA,
        next_step="user_match",
        validate_user_input=_validate_input,
    ),
    "user_match": SchemaFlowFormStep(
        CONFIG_OPTIONS_SCHEMA_MATCH,
        next_step="user_extra",
        validate_user_input=_validate_input,
    ),
    "user_extra": SchemaFlowFormStep(
        CONFIG_OPTIONS_SCHEMA_EXTRA,
        validate_user_input=_validate_input,
    ),
}

OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(
        CONFIG_OPTIONS_SCHEMA,
        validate_user_input=_validate_input,
        next_step="init_match",
    ),
    "init_match": SchemaFlowFormStep(
        CONFIG_OPTIONS_SCHEMA_MATCH,
        next_step="init_extra",
        validate_user_input=_validate_input,
    ),
    "init_extra": SchemaFlowFormStep(
        CONFIG_OPTIONS_SCHEMA_EXTRA,
        validate_user_input=_validate_input,
    ),
}


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle a config or options flow."""

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""

        return cast(str, DOMAIN_NAME)
