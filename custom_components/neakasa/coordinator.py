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

from .api import NeakasaAPI, APIAuthError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class NeakasaAPIData:
    """Class to hold api data."""

    binFullWaitReset: bool
    sandLevelPercent: int
    bucketStatus: bool
    room_of_bin: bool
    youngCatMode: bool
    childLockOnOff: bool
    autoBury: bool
    autoLevel: bool
    silentMode: bool


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
            update_interval=timedelta(seconds=10),
        )

        # Initialise api here
        self.api = NeakasaAPI(self.hass)

    async def setProperty(self, key: str, value: int):
        await self.api.connect(self.username, self.password)
        await self.api.setDeviceProperties(self.deviceid, {key: value})
        #update data
        devicedata = await self.api.getDeviceProperties(self.deviceid)
        self.async_set_updated_data(NeakasaAPIData(
            binFullWaitReset=devicedata['binFullWaitReset']['value'] == 1, #done
            sandLevelPercent=devicedata['Sand']['value']['percent'], #done
            bucketStatus=devicedata['bucketStatus']['value'] == 1, #done
            room_of_bin=devicedata['room_of_bin']['value'] == 1, #done
            youngCatMode=devicedata['youngCatMode']['value'] == 1, #done
            childLockOnOff=devicedata['childLockOnOff']['value'] == 1, #done
            autoBury=devicedata['autoBury']['value'] == 1, #done
            autoLevel=devicedata['autoLevel']['value'] == 1, #done
            silentMode=devicedata['silentMode']['value'] == 1 #done
        ))

    async def async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            await self.api.connect(self.username, self.password)
            devicedata = await self.api.getDeviceProperties(self.deviceid)
            return NeakasaAPIData(
                binFullWaitReset=devicedata['binFullWaitReset']['value'] == 1, #done
                sandLevelPercent=devicedata['Sand']['value']['percent'], #done
                bucketStatus=devicedata['bucketStatus']['value'] == 1, #done
                room_of_bin=devicedata['room_of_bin']['value'] == 1, #done
                youngCatMode=devicedata['youngCatMode']['value'] == 1,
                childLockOnOff=devicedata['childLockOnOff']['value'] == 1,
                autoBury=devicedata['autoBury']['value'] == 1,
                autoLevel=devicedata['autoLevel']['value'] == 1,
                silentMode=devicedata['silentMode']['value'] == 1
            )
        except APIAuthError as err:
            _LOGGER.error(err)
            raise UpdateFailed(err) from err
        except Exception as err:
            # This will show entities as unavailable by raising UpdateFailed exception
            raise UpdateFailed(f"Error communicating with API: {err}") from err
