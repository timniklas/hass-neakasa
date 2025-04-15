from dataclasses import dataclass, field
from datetime import timedelta
import logging
from typing import Optional, Any, Awaitable, Callable

from datetime import datetime

_LOGGER = logging.getLogger(__name__)

class ValueCacher:
    def __init__(self, refresh_after: Optional[timedelta], discard_after: Optional[timedelta]):
        """
        :param refresh_after:
            How long to wait before considering the cached value stale and needing refresh.
            - None: value never considered stale
            - timedelta <= 0: always considered stale
            - > 0: value is stale after this duration

        :param discard_after:
            How long to keep the cached value before discarding it entirely.
            - None: value never discarded (always acceptable as fallback)
            - timedelta <= 0: value is immediately discarded
            - > 0: value is discarded after this duration
        """
        self._refresh_after = refresh_after
        self._discard_after = discard_after

        self._manually_marked_stale = False

        self._value: Optional[Any] = None
        self._last_update: Optional[datetime] = None

    def set(self, value: Any) -> None:
        self._value = value
        self._last_update = datetime.utcnow()
        self._manually_marked_stale = False

    def clear(self) -> None:
        self._value = None
        self._last_update = None
        self._manually_marked_stale = False

    def mark_as_stale(self) -> None:
        self._manually_marked_stale = True

    def value_if_not_stale(self) -> Optional[Any]:
        """
        Return the value only if it is still fresh (not past refresh_after).
        Useful when you want to use cached data only if it's up-to-date.
        """
        if self._manually_marked_stale:
            return None
        if self._value is None or self._last_update is None:
            return None
        if self._refresh_after is not None:
            if self._refresh_after <= timedelta(0):
                return None
            if datetime.utcnow() - self._last_update > self._refresh_after:
                return None
        return self._value

    def value_if_not_discarded(self) -> Optional[Any]:
        """
        Return the value only if it hasn't been discarded.
        Discarding is based on discard_after.
        """
        if self._value is None or self._last_update is None:
            return None
        if self._discard_after is not None:
            if self._discard_after <= timedelta(0):
                return None
            if datetime.utcnow() - self._last_update > self._discard_after:
                return None
        return self._value

    async def get_or_update(self, update_func: Callable[[], Awaitable[Any]]) -> Any:
        """
        Return cached value if not stale. Otherwise, call `update_func` to get new value.
        If update fails, returns cached value if not discarded. Otherwise raises the error.
        """
        if (value := self.value_if_not_stale()) is not None:
            return value
        try:
            new_value = await update_func()
            self.set(new_value)
            return new_value
        except Exception as err:
            if (fallback := self.value_if_not_discarded()) is not None:
                return fallback
            raise err
