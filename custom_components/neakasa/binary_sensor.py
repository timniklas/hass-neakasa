import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import (
    STATE_ON,
    STATE_OFF,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NeakasaCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Sensors."""
    # This gets the data update coordinator from hass.data as specified in your __init__.py
    coordinator: NeakasaCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ].coordinator

    # Enumerate all the sensors in your data value from your DataUpdateCoordinator and add an instance of your sensor class
    # to a list for each one.
    # This maybe different in your specific case, depending on how your data is structured
    sensors = [
        NeakasaBinarySensor(coordinator, DeviceInfo(
            #only generate device once!
            name=coordinator.devicename,
            manufacturer="Neakasa",
            identifiers={(DOMAIN, coordinator.deviceid)}
        ), translation="bin_full_wait_reset", key="binFullWaitReset"),
        NeakasaBinarySensor(coordinator, DeviceInfo(
            identifiers={(DOMAIN, coordinator.deviceid)}
        ), translation="bucket_status", key="bucketStatus"),
        NeakasaBinarySensor(coordinator, DeviceInfo(
            identifiers={(DOMAIN, coordinator.deviceid)}
        ), translation="room_of_bin", key="room_of_bin", visible=False)
    ]

    # Create the sensors.
    async_add_entities(sensors)

class NeakasaBinarySensor(CoordinatorEntity):
    
    _attr_should_poll = False
    _attr_has_entity_name = True
    
    def __init__(self, coordinator: NeakasaCoordinator, deviceinfo: DeviceInfo, translation: str, key: str, visible: bool = True) -> None:
        super().__init__(coordinator)
        self.device_info = deviceinfo
        self.data_key = key
        self.translation_key = translation
        self.entity_registry_enabled_default = visible
        self.unique_id = f"{coordinator.deviceid}-{key}"

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return the state of the sensor."""
        return getattr(self.coordinator.data, self.data_key)
    
    @property
    def state(self):
        return STATE_ON if self.is_on else STATE_OFF
