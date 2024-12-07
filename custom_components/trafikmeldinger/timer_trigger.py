"""Timer trigger class."""

from datetime import datetime

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import CALLBACK_TYPE, Event, State, callback
from homeassistant.helpers import issue_registry as ir, start
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, DOMAIN_NAME

# ------------------------------------------------------

TRANSLATION_KEY_MISSING__TIMER_ENTITY = "missing_timer_entity"


# ------------------------------------------------------
# ------------------------------------------------------
class TimerTrigger:
    """Timer trigger class."""

    restarting_timer: bool = False

    def __init__(
        self,
        entity: Entity,
        timer_entity: str,
        callback_trigger: CALLBACK_TYPE,
        auto_restart: bool = True,
    ) -> None:
        """Init."""

        self.entity: Entity = entity
        self.timer_entity: str = timer_entity
        self.callback_trigger: CALLBACK_TYPE = callback_trigger
        self.auto_restart: bool = auto_restart

        self.error: bool = False
        self.timer_state: State

        self.entity.async_on_remove(
            self.entity.hass.bus.async_listen(
                "timer.finished", self.async_handle_timer_finished
            )
        )

        self.entity.async_on_remove(
            start.async_at_started(self.entity.hass, self.async_hass_started)
        )

    # ------------------------------------------------------------------
    async def async_validate_timer(self) -> bool:
        """Validate timer."""

        state: State = self.entity.hass.states.get(self.timer_entity)

        if state is None:
            self.error = True

            ir.async_create_issue(
                self.entity.hass,
                DOMAIN,
                DOMAIN_NAME + datetime.now().isoformat(),
                issue_domain=DOMAIN,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=TRANSLATION_KEY_MISSING__TIMER_ENTITY,
                translation_placeholders={
                    "timer_entity": self.timer_entity,
                    "entity": self.entity.entity_id,
                },
            )
            await self.callback_trigger(True)

            return False

        return True

    # ------------------------------------------------------------------
    async def async_restart_timer(self) -> bool:
        """Restart timer."""

        if self.error:
            return False

        state: State = self.entity.hass.states.get(self.timer_entity)

        if (
            state.state == "idle"
            and not TimerTrigger.restarting_timer
            and self.auto_restart
        ):
            TimerTrigger.restarting_timer = True

            await self.entity.hass.services.async_call(
                "timer",
                "start",
                service_data={ATTR_ENTITY_ID: self.timer_entity},
                blocking=True,
            )
            TimerTrigger.restarting_timer = False
        return True

    # ------------------------------------------------------------------
    @callback
    async def async_handle_timer_finished(self, event: Event) -> None:
        """Handle timer finished."""

        if not self.error and event.data[ATTR_ENTITY_ID] == self.timer_entity:
            if self.auto_restart:
                if await self.async_validate_timer():
                    await self.async_restart_timer()
        await self.callback_trigger(self.error)

    # ------------------------------------------------------
    async def async_hass_started(self, _event: Event) -> None:
        """Hass started."""

        if await self.async_validate_timer():
            if self.auto_restart:
                await self.async_restart_timer()
