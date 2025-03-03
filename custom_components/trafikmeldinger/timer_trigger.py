"""Timer trigger class."""

from datetime import datetime, timedelta
import inspect

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import CALLBACK_TYPE, Event, State, callback
from homeassistant.helpers import issue_registry as ir, start
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import Callable, dt as dt_util

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
        timer_entity: str = "",
        duration: timedelta | None = None,
        callback_trigger: CALLBACK_TYPE = None,
        auto_restart: bool = True,
    ) -> None:
        """Init."""

        if (timer_entity == "" and duration is None) or (
            timer_entity == ""
            and duration is not None
            and duration.total_seconds() <= 0
        ):
            raise ValueError("timer_entity or duration must be provided")

        self.entity: Entity = entity
        self.timer_entity: str = timer_entity
        self.duration: timedelta | None = duration
        self.callback_trigger: CALLBACK_TYPE = callback_trigger
        self.auto_restart: bool = auto_restart

        self.error: bool = False
        self.timer_state: State
        self.unsub_async_track_point_in_utc_time: Callable[[], None] | None = None

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
            if inspect.iscoroutinefunction(self.callback_trigger):
                await self.callback_trigger(self.error)
            else:
                self.callback_trigger(self.error)

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
    async def async_point_in_time_listener(self, time_date: datetime) -> None:
        """Point in time listener."""

        if self.unsub_async_track_point_in_utc_time:
            self.unsub_async_track_point_in_utc_time()
            self.unsub_async_track_point_in_utc_time = None

        if inspect.iscoroutinefunction(self.callback_trigger):
            await self.callback_trigger(self.error)
        else:
            self.callback_trigger(self.error)

        self.point_in_time_listener_start()

    # ------------------------------------------------------------------
    def point_in_time_listener_start(self) -> None:
        """Point in time listener start."""

        if not self.error:
            self.unsub_async_track_point_in_utc_time = async_track_point_in_utc_time(
                self.entity.hass,
                self.async_point_in_time_listener,
                dt_util.utcnow() + self.duration,
            )

    # ------------------------------------------------------------------
    @callback
    async def async_handle_timer_finished(self, event: Event) -> None:
        """Handle timer finished."""

        if inspect.iscoroutinefunction(self.callback_trigger):
            await self.callback_trigger(self.error)
        else:
            self.callback_trigger(self.error)

        if not self.error and event.data[ATTR_ENTITY_ID] == self.timer_entity:
            if self.auto_restart:
                if await self.async_validate_timer():
                    await self.async_restart_timer()

    # ------------------------------------------------------
    async def async_hass_started(self, _event: Event) -> None:
        """Hass started."""

        if self.timer_entity != "":
            if await self.async_validate_timer():
                self.entity.async_on_remove(
                    self.entity.hass.bus.async_listen(
                        "timer.finished", self.async_handle_timer_finished
                    )
                )

                if self.auto_restart:
                    await self.async_restart_timer()

        else:
            self.unsub_async_track_point_in_utc_time = async_track_point_in_utc_time(
                self.entity.hass,
                self.async_point_in_time_listener,
                dt_util.utcnow() + self.duration,
            )
