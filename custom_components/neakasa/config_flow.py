import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from aiohttp import ClientError, ClientResponseError, ClientSession, BasicAuth
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_FRIENDLY_NAME,
    CONF_USERNAME,
    CONF_PASSWORD,
)
from .api import NeakasaAPI, APIAuthError, APIConnectionError
from .const import DOMAIN

class NeakasaConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._username: None = None
        self._password: None = None
        self._discovered_devices: dict[str, str] = {}

    async def async_step_user(self, formdata):
        if formdata is not None:
            self._username = formdata[CONF_USERNAME]
            self._password = formdata[CONF_PASSWORD]
            try:
                session = async_get_clientsession(self.hass)
                api = NeakasaAPI(session, self.hass.async_add_executor_job)
                await api.connect(self._username, self._password)

                devices = await api.getDevices()
                discovered_devices = {}
                for device in list(filter(lambda device: device['categoryKey'] == 'CatLitter', devices)):
                    deviceName = device['deviceName']
                    deviceId = device['iotId']
                    discovered_devices[deviceId] = deviceName
                self._discovered_devices = discovered_devices
                return await self.async_step_device(None)
            except APIAuthError as exc:
                return self.async_abort(reason="authentication")
            except APIConnectionError as exc:
                return self.async_abort(reason="connenction")
        
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str
            })
        )

    async def async_step_device(self, formdata):
        if formdata is not None:
            deviceid = formdata[CONF_DEVICE_ID]
            await self.async_set_unique_id(deviceid, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            data = {}
            data[CONF_DEVICE_ID] = deviceid
            data[CONF_FRIENDLY_NAME] = self._discovered_devices[deviceid]
            data[CONF_USERNAME] = self._username
            data[CONF_PASSWORD] = self._password
            return self.async_create_entry(title=self._discovered_devices[deviceid], data=data)

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")
        
        return self.async_show_form(
            step_id="device", data_schema=vol.Schema(
                {vol.Required(CONF_DEVICE_ID): vol.In(self._discovered_devices)}
            ),
        )
