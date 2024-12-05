import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS, UnitOfTime
from datetime import datetime

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
        ), translation="sand_percent", key="sandLevelPercent", unit=PERCENTAGE),
        NeakasaSensor(coordinator, DeviceInfo(
            identifiers={(DOMAIN, coordinator.deviceid)}
        ), translation="wifi_rssi", key="wifiRssi", unit=SIGNAL_STRENGTH_DECIBELS, visible=False, icon="mdi:wifi"),
        NeakasaSensor(coordinator, DeviceInfo(
            identifiers={(DOMAIN, coordinator.deviceid)}
        ), translation="stay_time", key="stayTime", unit=UnitOfTime.SECONDS, visible=False),
        NeakasaTimestampSensor(coordinator, DeviceInfo(
            identifiers={(DOMAIN, coordinator.deviceid)}
        ), translation="last_usage", key="lastUse"),
        NeakasaMapSensor(coordinator, DeviceInfo(
            identifiers={(DOMAIN, coordinator.deviceid)}
        ), translation="current_status", key="bucketStatus", options=['idle', 'cleaning', 'cleaning', 'leveling'], icon="mdi:state-machine"),
        NeakasaMapSensor(coordinator, DeviceInfo(
            identifiers={(DOMAIN, coordinator.deviceid)}
        ), translation="sand_state", key="sandLevelState", options=['insufficient', 'moderate', 'sufficient']),
        NeakasaMapSensor(coordinator, DeviceInfo(
            identifiers={(DOMAIN, coordinator.deviceid)}
        ), translation="bin_state", key="room_of_bin", options=['normal', None, 'missing'], icon="mdi:delete")
    ]

    # Create the sensors.
    async_add_entities(sensors)

class NeakasaSensor(CoordinatorEntity):
    
    _attr_should_poll = False
    _attr_has_entity_name = True
    
    def __init__(self, coordinator: NeakasaCoordinator, deviceinfo: DeviceInfo, translation: str, key: str, unit: str, icon: str = None, visible: bool = True) -> None:
        super().__init__(coordinator)
        self.device_info = deviceinfo
        self.data_key = key
        self.translation_key = translation
        self.entity_registry_enabled_default = visible
        self._attr_unique_id = f"{coordinator.deviceid}-{translation}"
        self._attr_unit_of_measurement = unit
        if icon is not None:
            self._attr_icon = icon

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
    
    @property
    def state(self):
        return getattr(self.coordinator.data, self.data_key)
    
    @property
    def extra_state_attributes(self):
        return {
            "state_class": SensorStateClass.MEASUREMENT
        }

class NeakasaMapSensor(CoordinatorEntity):
    
    _attr_should_poll = False
    _attr_has_entity_name = True
    
    def __init__(self, coordinator: NeakasaCoordinator, deviceinfo: DeviceInfo, translation: str, key: str, options: list, icon: str = None, visible: bool = True) -> None:
        super().__init__(coordinator)
        self.device_info = deviceinfo
        self.data_key = key
        self.translation_key = translation
        self.entity_registry_enabled_default = visible
        self._attr_unique_id = f"{coordinator.deviceid}-{translation}"
        self.key_options = options
        if icon is not None:
            self._attr_icon = icon

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
    
    @property
    def state(self):
        value = getattr(self.coordinator.data, self.data_key)
        if value >= len(self.key_options):
            return None
        return self.key_options[value]

class NeakasaTimestampSensor(CoordinatorEntity):
    
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    
    def __init__(self, coordinator: NeakasaCoordinator, deviceinfo: DeviceInfo, translation: str, key: str, icon: str = None, visible: bool = True) -> None:
        super().__init__(coordinator)
        self.device_info = deviceinfo
        self.data_key = key
        self.translation_key = translation
        self.entity_registry_enabled_default = visible
        self._attr_unique_id = f"{coordinator.deviceid}-{translation}"
        if icon is not None:
            self._attr_icon = icon

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
    
    @property
    def state(self):
        timestamp = getattr(self.coordinator.data, self.data_key) / 1000
        return datetime.fromtimestamp(timestamp)
