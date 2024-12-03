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
from homeassistant.const import PERCENTAGE

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
        NeakasaSensor(coordinator, DeviceInfo(
            identifiers={(DOMAIN, coordinator.deviceid)}
        ), translation="sand_level_percent", key="sandLevelPercent")
    ]

    # Create the sensors.
    async_add_entities(sensors)

class NeakasaSensor(CoordinatorEntity):
    
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_unit_of_measurement = PERCENTAGE
    
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
    def state(self):
        return getattr(self.coordinator.data, self.data_key)
