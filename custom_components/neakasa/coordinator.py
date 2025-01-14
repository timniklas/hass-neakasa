from dataclasses import dataclass
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_FRIENDLY_NAME,
    CONF_USERNAME,
    CONF_PASSWORD,
)
from homeassistant.core import HomeAssistant
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
        self.api = NeakasaAPI(self.hass)
        

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

    async def async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            await self.api.connect(self.username, self.password)
            devicedata = await self.api.getDeviceProperties(self.deviceid)
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
                lastUse=devicedata['catLeft']['time']
            )
        except APIAuthError as err:
            raise UpdateFailed(err) from err
        except APIConnectionError as err:
            raise UpdateFailed(err) from err
