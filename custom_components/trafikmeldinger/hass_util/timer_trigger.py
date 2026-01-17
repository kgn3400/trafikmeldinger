"""Timer trigger.

External imports: None
"""

from datetime import datetime, timedelta
from enum import Enum
import inspect

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import Event, State, callback
from homeassistant.helpers import start
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import Callable, dt as dt_util


# ------------------------------------------------------
# ------------------------------------------------------
class TimerTriggerErrorEnum(Enum):
    """Error to indicate unknown timer helper."""

    NONE = 0
    MISSING_TIMER_ENTITY = 1
    UNKNOWN_ERROR = 2
    PARAMETER_ERROR = 4

    # ------------------------------------------------------

    def __bool__(self):
        """Return if error."""
        return self != TimerTriggerErrorEnum.NONE


# ------------------------------------------------------
# ------------------------------------------------------
class TimerTrigger:
    """Timer trigger class.

    External imports: None

    """

    restarting_timer: bool = False

    def __init__(
        self,
        entity: Entity,
        timer_entity: str = "",
        duration: timedelta | None = None,
        callback_trigger: Callable[[TimerTriggerErrorEnum], None] = None,
        auto_restart: bool = True,
        # auto_start: bool = True, # TODO: Add auto_start
    ) -> None:
        """Init."""

        if (timer_entity == "" and duration is None) or (
            timer_entity == ""
            and duration is not None
            and duration.total_seconds() <= 0
        ):
            self.error = TimerTriggerErrorEnum.PARAMETER_ERROR
            raise ValueError("timer_entity or duration must be provided")

        if callback_trigger is None:
            self.error = TimerTriggerErrorEnum.PARAMETER_ERROR
            raise ValueError("callback_trigger must be provided")

        self.entity: Entity = entity
        self.timer_entity: str = timer_entity
        self.duration: timedelta | None = duration
        self.callback_trigger: Callable[[TimerTriggerErrorEnum], None] | None = (
            callback_trigger
        )
        self.auto_restart: bool = auto_restart
        self.auto_start: bool = True

        self.error: TimerTriggerErrorEnum = TimerTriggerErrorEnum.NONE
        self.point_in_UTC_time_trigger: PointInUTCTimeTrigger | None = None

        self.entity.async_on_remove(
            start.async_at_started(self.entity.hass, self.async_hass_started)
        )

    # ------------------------------------------------------------------
    async def async_validate_timer(self) -> bool:
        """Validate timer."""

        state: State = self.entity.hass.states.get(self.timer_entity)

        if state is None:
            self.error = TimerTriggerErrorEnum.MISSING_TIMER_ENTITY

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
            self.point_in_UTC_time_trigger = PointInUTCTimeTrigger(
                self.entity,
                duration=self.duration,
                callback_trigger=self.async_point_in_time_callback,
                auto_restart=self.auto_restart,
                auto_start=self.auto_start,
            )

    # ------------------------------------------------------
    async def async_point_in_time_callback(self) -> None:
        """Point in time callback."""

        if inspect.iscoroutinefunction(self.callback_trigger):
            await self.callback_trigger(self.error)
        else:
            self.callback_trigger(self.error)


# ------------------------------------------------------
# ------------------------------------------------------
class PointInUTCTimeTrigger:
    """Point in UTC time trigger class.

    NB. Reuse the same PointInUTCTimeTrigger object.

    External imports: None

    """

    def __init__(
        self,
        entity: Entity,
        point_in_time_UTC: datetime | None = None,
        duration: timedelta | None = None,
        callback_trigger: Callable[[], None] = None,
        auto_restart: bool = False,
        auto_start: bool = False,
    ) -> None:
        """Init."""

        self.entity: Entity = entity
        self.point_in_time_UTC: datetime | None = point_in_time_UTC
        self.duration: timedelta | None = duration
        self.callback_trigger: Callable[[], None] | None = callback_trigger
        self.auto_restart: bool = auto_restart
        self.auto_start: bool = auto_start

        self.error: TimerTriggerErrorEnum = TimerTriggerErrorEnum.NONE
        self.unsub_async_track_point_in_utc_time: Callable[[], None] | None = None

        self.entity.async_on_remove(
            start.async_at_started(self.entity.hass, self.async_hass_started)
        )

    # ------------------------------------------------------
    def start(
        self,
        point_in_time_UTC: datetime | None = None,
        duration: timedelta | None = None,
        callback_trigger: Callable[[], None] = None,
        auto_restart: bool | None = None,
    ) -> datetime | None:
        """Start point in UTC time trigger."""

        if point_in_time_UTC is not None:
            self.point_in_time_UTC = point_in_time_UTC

        if duration is not None:
            self.duration = duration

        if callback_trigger is not None:
            self.callback_trigger = callback_trigger

        if auto_restart is not None:
            self.auto_restart = auto_restart

        return self.point_in_time_listener_start()

    # ------------------------------------------------------
    async def async_hass_started(self, _event: Event) -> None:
        """Hass started."""

        self.entity.async_on_remove(self.async_remove_from_hass)

        if not self.auto_start:
            return

        self.point_in_time_listener_start()

    # ------------------------------------------------------
    @callback
    def async_remove_from_hass(self) -> None:
        """Handle removal from Hass."""

        if self.unsub_async_track_point_in_utc_time:
            self.unsub_async_track_point_in_utc_time()
            self.unsub_async_track_point_in_utc_time = None

    # ------------------------------------------------------------------
    async def async_point_in_time_listener(self, time_date: datetime) -> None:
        """Point in time listener."""

        if self.error:
            return

        if inspect.iscoroutinefunction(self.callback_trigger):
            await self.callback_trigger()
        else:
            self.callback_trigger()

        if self.auto_restart:
            self.point_in_time_listener_start()

    # ------------------------------------------------------------------
    def point_in_time_listener_start(self) -> datetime | None:
        """Point in time listener start."""

        if self.error:
            return None

        if self.unsub_async_track_point_in_utc_time:
            self.unsub_async_track_point_in_utc_time()
            self.unsub_async_track_point_in_utc_time = None

        if self.duration is None and self.point_in_time_UTC is None:
            self.error = TimerTriggerErrorEnum.PARAMETER_ERROR
            raise ValueError("point_in_time_UTC or duration must be provided")

        if self.duration is not None and self.duration.total_seconds() <= 0:
            self.error = TimerTriggerErrorEnum.PARAMETER_ERROR
            raise ValueError("duration under 0 is not allowed")

        if (
            self.point_in_time_UTC is not None
            and self.point_in_time_UTC < dt_util.utcnow()
        ):
            self.error = TimerTriggerErrorEnum.PARAMETER_ERROR
            raise ValueError("point_in_time_UTC in the past is not allowed")

        if self.callback_trigger is None:
            self.error = TimerTriggerErrorEnum.PARAMETER_ERROR
            raise ValueError("callback_trigger must be provided")

        tmp_datetime: datetime

        if self.point_in_time_UTC:
            self.unsub_async_track_point_in_utc_time = async_track_point_in_utc_time(
                self.entity.hass,
                self.async_point_in_time_listener,
                self.point_in_time_UTC,
            )
            tmp_datetime = self.point_in_time_UTC
        else:
            tmp_datetime = dt_util.utcnow() + self.duration
            self.unsub_async_track_point_in_utc_time = async_track_point_in_utc_time(
                self.entity.hass,
                self.async_point_in_time_listener,
                tmp_datetime,
            )

        return tmp_datetime
