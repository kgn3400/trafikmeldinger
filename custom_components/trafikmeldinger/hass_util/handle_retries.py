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
    """Exception to stop retrying.

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
    ):
        """Init.

        Args:
            retries (int, optional): _description_. Defaults to 0.
            retry_delay (float, optional): _description_. Defaults to 0.0.
            raise_last_exception (bool, optional): _description_. Defaults to True.
            raise_original_exception (bool, optional): _description_. Defaults to True.

        """
        self.retries: int = retries if retries > 0 else 1
        self.retry_delay: float = retry_delay if retry_delay > 0 else 0.0
        self.raise_last_exception: bool = raise_last_exception
        self.raise_original_exception: bool = raise_original_exception

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
            @wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(self.retries):
                    try:
                        return func(*args, **kwargs)
                    except RetryStopException:
                        raise
                    except Exception as err:
                        if attempt == self.retries - 1:
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
                        if attempt == self.retries - 1:
                            if self.raise_last_exception:
                                if self.raise_original_exception:
                                    raise
                                raise HandleRetriesException(
                                    f"Retry {attempt} failed for {func.__name__}"
                                ) from err
                    await asyncio_sleep(self.retry_delay)
                return None

            # Check if the function is a coroutine function
            # and return the appropriate wrapper
            # to handle async functions
            # and sync functions
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
        """Ascync execute.

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
            ).execute(func, *args, **kwargs)
            # for attempt in range(retries):
            #     try:
            #         return func(*args, **kwargs)
            #     except RetryStopException:
            #         raise
            #     except Exception as err:
            #         if attempt == retries - 1:
            #             if raise_last_exception:
            #                 if raise_original_exception:
            #                     raise
            #                 raise HandleRetriesException(
            #                     f"Retry {attempt} failed for {func.__name__}"
            #                 ) from err
            #     sleep(retry_delay)
            # return None

        # -------------------------
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await HandleRetries(
                retries=retries,
                retry_delay=retry_delay,
                raise_last_exception=raise_last_exception,
                raise_original_exception=raise_original_exception,
            ).async_execute(func, *args, **kwargs)

            # for attempt in range(retries):
            #     try:
            #         return await func(*args, **kwargs)
            #     except RetryStopException:
            #         raise
            #     except Exception as err:
            #         if attempt == retries - 1:
            #             if raise_last_exception:
            #                 if raise_original_exception:
            #                     raise
            #                 raise HandleRetriesException(
            #                     f"Retry {attempt} failed for {func.__name__}"
            #                 ) from err
            #     await asyncio_sleep(retry_delay)
            # return None

        # Check if the function is a coroutine function
        # and return the appropriate wrapper
        # to handle async functions
        # and sync functions
        if iscoroutinefunction(func):
            return async_wrapper

        return wrapper

    return decorator_wrap(func)
