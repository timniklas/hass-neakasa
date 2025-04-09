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
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS, UnitOfTime, EntityCategory, UnitOfMass
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
    device_info = DeviceInfo(
        name=coordinator.devicename,
        manufacturer="Neakasa",
        identifiers={(DOMAIN, coordinator.deviceid)}
    )
    # Enumerate all the sensors in your data value from your DataUpdateCoordinator and add an instance of your sensor class
    # to a list for each one.
    # This maybe different in your specific case, depending on how your data is structured
    sensors = [
        NeakasaSensor(coordinator, device_info, translation="sand_percent", key="sandLevelPercent", unit=PERCENTAGE),
        NeakasaSensor(coordinator, device_info, translation="wifi_rssi", key="wifiRssi", unit=SIGNAL_STRENGTH_DECIBELS, visible=False, category=EntityCategory.DIAGNOSTIC, icon="mdi:wifi"),
        NeakasaSensor(coordinator, device_info, translation="stay_time", key="stayTime", unit=UnitOfTime.SECONDS, visible=False),
        NeakasaTimestampSensor(coordinator, device_info, translation="last_usage", key="lastUse"),
        NeakasaMapSensor(coordinator, device_info, translation="current_status", key="bucketStatus", options=['idle', 'cleaning', 'cleaning', 'leveling', 'flipover', 'cat_present'], icon="mdi:state-machine"),
        NeakasaMapSensor(coordinator, device_info, translation="sand_state", key="sandLevelState", options=['insufficient', 'moderate', 'sufficient', 'overfilled']),
        NeakasaMapSensor(coordinator, device_info, translation="bin_state", key="room_of_bin", options=['normal', 'full', 'missing'], icon="mdi:delete")
    ]

    for cat in coordinator.data.cat_list:
        sensors.append(
            NeakasaCatSensor(coordinator, device_info, catName=cat['name'], catId=cat['id'], icon="mdi:cat")
        )

    # Create the sensors.
    async_add_entities(sensors)

class NeakasaCatSensor(CoordinatorEntity):
    
    _attr_should_poll = False
    _attr_has_entity_name = True
    
    def __init__(self, coordinator: NeakasaCoordinator, deviceinfo: DeviceInfo, catName: str, catId: str, icon: str = None, visible: bool = True, category: str = None) -> None:
        super().__init__(coordinator)
        self.device_info = deviceinfo
        self.entity_registry_enabled_default = visible
        self._attr_translation_key = "cat_sensor"
        self._attr_translation_placeholders = {"name": catName}
        self._attr_unique_id = f"{coordinator.deviceid}-cat-{catId}"
        self._attr_unit_of_measurement = UnitOfMass.KILOGRAMS
        self._catId = catId
        if icon is not None:
            self._attr_icon = icon
        if category is not None:
            self._attr_entity_category = category

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
    
    @property
    def _records(self):
        return list(filter(lambda record: record['cat_id'] == self._catId, self.coordinator.data.record_list))

    @property
    def state(self):
        last_record = self._records[-1]
        return last_record['weight']
    
    @property
    def extra_state_attributes(self):
        last_record = self._records[-1]
        return {
            "state_class": SensorStateClass.MEASUREMENT,
            "start_time": datetime.fromtimestamp(last_record['start_time']),
            "end_time": datetime.fromtimestamp(last_record['end_time'])
        }

class NeakasaSensor(CoordinatorEntity):
    
    _attr_should_poll = False
    _attr_has_entity_name = True
    
    def __init__(self, coordinator: NeakasaCoordinator, deviceinfo: DeviceInfo, translation: str, key: str, unit: str, icon: str = None, visible: bool = True, category: str = None) -> None:
        super().__init__(coordinator)
        self.device_info = deviceinfo
        self.data_key = key
        self.translation_key = translation
        self.entity_registry_enabled_default = visible
        self._attr_unique_id = f"{coordinator.deviceid}-{translation}"
        self._attr_unit_of_measurement = unit
        if icon is not None:
            self._attr_icon = icon
        if category is not None:
            self._attr_entity_category = category

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
