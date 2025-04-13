from dataclasses import dataclass, field
from datetime import timedelta
import logging
from typing import Optional, Any, Awaitable, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_FRIENDLY_NAME,
    CONF_USERNAME,
    CONF_PASSWORD,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import datetime

from .api import NeakasaAPI, APIAuthError, APIConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class NeakasaAPIData:
    """Class to hold api data."""

    binFullWaitReset: bool
    sandLevelState: int
    sandLevelPercent: int
    bucketStatus: int
    room_of_bin: int
    youngCatMode: bool
    childLockOnOff: bool
    autoBury: bool
    autoLevel: bool
    silentMode: bool
    wifiRssi: int
    autoForceInit: bool
    bIntrptRangeDet: bool
    stayTime: int
    lastUse: int
    cat_list: list[object] = field(default_factory=list)
    record_list: list[object] = field(default_factory=list)
    statistics: list[object] = field(default_factory=list)

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
        self._value: Optional[Any] = None
        self._last_update: Optional[datetime] = None

    def set(self, value: Any) -> None:
        self._value = value
        self._last_update = datetime.utcnow()

    def clear(self) -> None:
        self._value = None
        self._last_update = None

    def value_if_not_stale(self) -> Optional[Any]:
        """
        Return the value only if it is still fresh (not past refresh_after).
        Useful when you want to use cached data only if it's up-to-date.
        """
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

class NeakasaCoordinator(DataUpdateCoordinator):
    """My coordinator."""

    data: NeakasaAPIData

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        # Set variables from values entered in config flow setup
        self.deviceid = config_entry.data[CONF_DEVICE_ID]
        self.devicename = config_entry.data[CONF_FRIENDLY_NAME]
        self.username = config_entry.data[CONF_USERNAME]
        self.password = config_entry.data[CONF_PASSWORD]

        self._deviceName = None

        self._statisticsCache = ValueCacher(refresh_after=timedelta(minutes=60), discard_after=timedelta(hours=7))
        self._recordsCache = ValueCacher(refresh_after=timedelta(minutes=30), discard_after=timedelta(hours=4))
        self._devicePropertiesCache = ValueCacher(refresh_after=timedelta(seconds=0), discard_after=timedelta(minutes=30))

        # Initialise DataUpdateCoordinator
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({config_entry.unique_id})",
            # Method to call on every update interval.
            update_method=self.async_update_data,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=60),
        )

        # Initialise api here
        session = async_get_clientsession(hass)
        self.api = NeakasaAPI(session, hass.async_add_executor_job)
        

    async def setProperty(self, key: str, value: int):
        await self.api.connect(self.username, self.password)
        await self.api.setDeviceProperties(self.deviceid, {key: value})
        #update data
        setattr(self.data, key, value)
        self.async_set_updated_data(self.data)

    async def invokeService(self, service: str):
        await self.api.connect(self.username, self.password)
        match service:
            case 'clean':
                return await self.api.cleanNow(self.deviceid)
            case 'level':
                return await self.api.sandLeveling(self.deviceid)
        raise Exception('cannot find service to invoke')

    async def _getDeviceName(self):
        if self._deviceName is not None:
            return self._deviceName

        """get deviceName by iotId"""
        await self.api.connect(self.username, self.password)
        devices = await self.api.getDevices()
        devices = list(filter(lambda devices: devices['iotId'] == self.deviceid, devices))
        if(len(devices) == 0):
            raise APIConnectionError("iotId not found in device list")
        deviceName = devices[0]['deviceName']
        self._deviceName = deviceName
        return deviceName

    async def _getStatistics(self):
        async def fetch():
            await self.api.connect(self.username, self.password)
            deviceName = await self._getDeviceName()
            return await self.api.getStatistics(deviceName)

        return await self._statisticsCache.get_or_update(fetch)

    async def _getRecords(self):
        async def fetch():
            await self.api.connect(self.username, self.password)
            deviceName = await self._getDeviceName()
            return await self.api.getRecords(deviceName)

        return await self._recordsCache.get_or_update(fetch)

    async def _getDeviceProperties(self):
        async def fetch():
            await self.api.connect(self.username, self.password)
            return await self.api.getDeviceProperties(self.deviceid)

        return await self._devicePropertiesCache.get_or_update(fetch)

    async def async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            statistics = await self._getStatistics()
            records = await self._getRecords()
            devicedata = await self._getDeviceProperties()
            try:
                return NeakasaAPIData(
                    binFullWaitReset=devicedata['binFullWaitReset']['value'] == 1, #-> Abfalleimer voll
                    youngCatMode=devicedata['youngCatMode']['value'] == 1, #-> Kätzchen Modus
                    childLockOnOff=devicedata['childLockOnOff']['value'] == 1, #-> Kindersicherung
                    autoBury=devicedata['autoBury']['value'] == 1, #-> automatische Abdeckung
                    autoLevel=devicedata['autoLevel']['value'] == 1, #-> automatische Nivellierung
                    silentMode=devicedata['silentMode']['value'] == 1, #-> Stiller Modus
                    autoForceInit=devicedata['autoForceInit']['value'] == 1, #-> automatische Wiederherstellung
                    bIntrptRangeDet=devicedata['bIntrptRangeDet']['value'] == 1, #-> Unaufhaltsamer Kreislauf
                    sandLevelPercent=devicedata['Sand']['value']['percent'], #-> Katzenstreu Prozent
                    wifiRssi=devicedata['NetWorkStatus']['value']['WiFi_RSSI'], #-> WLAN RSSI
                    bucketStatus=devicedata['bucketStatus']['value'], #-> Aktueller Status [0=Leerlauf,2=Reinigung,3=Nivellierung]
                    room_of_bin=devicedata['room_of_bin']['value'], #-> Abfalleimer [2=nicht in Position,0=Normal]
                    sandLevelState=devicedata['Sand']['value']['level'], #-> Katzenstreu [0=Unzureichend,1=Mäßig,2=Ausreichend]
                    stayTime=devicedata['catLeft']['value']['stayTime'],
                    lastUse=devicedata['catLeft']['time'],

                    cat_list=records['cat_list'],
                    record_list=records['record_list'],

                    statistics=statistics
                )
            except Exception as err:
                _LOGGER.error(err)
                # This will show entities as unavailable by raising UpdateFailed exception
                raise UpdateFailed(f"Got no data from api, please try to restart your litter box.") from err
        except APIAuthError as err:
            _LOGGER.error(err)
            raise UpdateFailed(err) from err
        except APIConnectionError as err:
            _LOGGER.error(err)
            raise UpdateFailed(err) from err
