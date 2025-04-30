"""Handle retries decorator for functions and async functions.

This decorator allows you to specify the number of retries and the delay between retries.
It can be used with both synchronous and asynchronous functions.

External imports: None
"""

from asyncio import sleep as asyncio_sleep
from collections.abc import Callable
from functools import partial, wraps
from inspect import iscoroutinefunction
from time import sleep


# ------------------------------------------------------
# ------------------------------------------------------
class RetryStopException(Exception):
    """Exception to stop retrying.

    Args:
        Exception (_type_): _description_

    """


# ------------------------------------------------------
# ------------------------------------------------------
class HandleRetriesException(Exception):
    """handle retries Exception.

    Args:
        Exception (_type_): _description_

    """


# ------------------------------------------------------
# ------------------------------------------------------
class HandleRetries:
    """Handle retries class.

    Decorator to handle retries.
    It will retry the function if it raises an exception up to a specified number of times, with a specified delay.
    It can be used with both synchronous and asynchronous functions.
    It will raise the last exception if the number of retries is reached and raise_last_exception is True.

    """

    def __init__(
        self,
        retries: int = 1,
        retry_delay: float = 0.0,
        raise_last_exception: bool = True,
        raise_original_exception: bool = True,
        retry_on_exceptions: list | None = None,
        stop_on_exceptions: list | None = None,
    ):
        """Init.

        Args:
            retries (int, optional): _description_. Defaults to 0.
            retry_delay (float, optional): _description_. Defaults to 0.0.
            raise_last_exception (bool, optional): _description_. Defaults to True.
            raise_original_exception (bool, optional): _description_. Defaults to True.
            retry_on_exceptions (list | Exception | None, optional): _description_. Defaults to None.
            stop_on_exceptions (list | Exception | None, optional): _description_. Defaults to None.

        """
        self.retries: int = retries if retries > 0 else 1
        self.retry_delay: float = retry_delay if retry_delay > 0 else 0.0
        self.raise_last_exception: bool = raise_last_exception
        self.raise_original_exception: bool = raise_original_exception
        self.retry_on_exceptions: list | None = retry_on_exceptions
        self.stop_on_exceptions: list | None = stop_on_exceptions

    # ------------------------------------------------------
    def __call__(self, func):
        """__call__.

        Args:
            func (_type_): _description_

        Raises:
            e: _description_
            e: _description_

        Returns:
            _type_: _description_

        """

        # -------------------------
        def decorator_wrap(func):
            # -------------------------
            def check_retry_on_exceptions(exp: Exception):
                """Check if the exception is in the retry_on_exceptions list."""
                if self.retry_on_exceptions is None:
                    return True

                if exp.__class__ in self.retry_on_exceptions:
                    return True

                return False

            # -------------------------
            def check_stop_on_exceptions(exp: Exception):
                """Check if the exception is in the stop_on_exceptions list."""
                if self.stop_on_exceptions is None:
                    return False

                if exp.__class__ in self.stop_on_exceptions:
                    return True

                return False

            # -------------------------
            @wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(self.retries):
                    try:
                        return func(*args, **kwargs)
                    except RetryStopException:
                        raise
                    except Exception as err:
                        if (
                            not check_retry_on_exceptions(err)
                            or check_stop_on_exceptions(err)
                            or attempt == self.retries - 1
                        ):
                            if self.raise_last_exception:
                                if self.raise_original_exception:
                                    raise
                                raise HandleRetriesException(
                                    f"Retry {attempt} failed for {func.__name__}"
                                ) from err

                    sleep(self.retry_delay)
                return None

            # -------------------------
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                for attempt in range(self.retries):
                    try:
                        return await func(*args, **kwargs)
                    except RetryStopException:
                        raise
                    except Exception as err:
                        if (
                            not check_retry_on_exceptions(err)
                            or check_stop_on_exceptions(err)
                            or attempt == self.retries - 1
                        ):
                            if self.raise_last_exception:
                                if self.raise_original_exception:
                                    raise
                                raise HandleRetriesException(
                                    f"Retry {attempt} failed for {func.__name__}"
                                ) from err
                    await asyncio_sleep(self.retry_delay)
                return None

            # Check if the function is a coroutine function
            if iscoroutinefunction(func):
                return async_wrapper

            return wrapper

        return decorator_wrap(func)

    # ------------------------------------------------------
    def execute(
        self,
        func: Callable,
        *args,
        **kwargs,
    ):
        """Execute.

        How to call: HandleRetries(retries=3, retry_delay=1).execute((test_func),"Hello world")
        """
        return self.__call__(func)(*args, **kwargs)

    # ------------------------------------------------------
    async def async_execute(
        self,
        func: Callable,
        *args,
        **kwargs,
    ):
        """Async execute.

        How to call: await HandleRetries(retries=3, retry_delay=1).async_execute((async_test_func),"Hello world")


        """
        return await self.__call__(func)(*args, **kwargs)


# ------------------------------------------------------
def handle_retries(
    func=None,
    *,
    retries: int = 5,
    retry_delay: float = 5.0,
    raise_last_exception: bool = True,
    raise_original_exception: bool = True,
    retry_on_exceptions: list | None = None,
    stop_on_exceptions: list | None = None,
):
    """Handle retries.

    Decorator to handle retries.
    It will retry the function if it raises an exception up to a specified number of times, with a specified delay.
    It can be used with both synchronous and asynchronous functions.
    It will raise the last exception if the number of retries is reached and raise_last_exception is True.

    Args:
        func (_type_, optional): _description_. Defaults to None.
        retries (int, optional): _description_. Defaults to 5.
        retry_delay (float, optional): _description_. Defaults to 5.0.
        raise_last_exception (bool, optional): _description_. Defaults to True.
        raise_original_exception (bool, optional): _description_. Defaults to True.
        retry_on_exceptions (list | Exception | None, optional): _description_. Defaults to None.
        stop_on_exceptions (list | Exception | None, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_

    """

    if func is None:
        return partial(
            handle_retries,
            retries=retries,
            retry_delay=retry_delay,
            raise_last_exception=raise_last_exception,
            raise_original_exception=raise_original_exception,
            retry_on_exceptions=retry_on_exceptions,
            stop_on_exceptions=stop_on_exceptions,
        )

    # -------------------------
    def decorator_wrap(func):
        # -------------------------
        @wraps(func)
        def wrapper(*args, **kwargs):
            return HandleRetries(
                retries=retries,
                retry_delay=retry_delay,
                raise_last_exception=raise_last_exception,
                raise_original_exception=raise_original_exception,
                retry_on_exceptions=retry_on_exceptions,
                stop_on_exceptions=stop_on_exceptions,
            ).execute(func, *args, **kwargs)

        # -------------------------
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await HandleRetries(
                retries=retries,
                retry_delay=retry_delay,
                raise_last_exception=raise_last_exception,
                raise_original_exception=raise_original_exception,
                retry_on_exceptions=retry_on_exceptions,
                stop_on_exceptions=stop_on_exceptions,
            ).async_execute(func, *args, **kwargs)

        # Check if the function is a coroutine function
        if iscoroutinefunction(func):
            return async_wrapper

        return wrapper

    return decorator_wrap(func)
