"""Lennox BLE Air Quality Sensor"""
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass

from homeassistant.const import SIGNAL_STRENGTH_DECIBELS_MILLIWATT, CONCENTRATION_PARTS_PER_MILLION

lennox_21p02_sensors = [
    {
        "input_id": 4000,
        "name": "rssi",
        "state_class": SensorStateClass.MEASUREMENT,
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "uom": SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    },
    {
        "input_id": 4003,
        "name": "total powered time",
        "state_class": SensorStateClass.MEASUREMENT,
        "device_class": SensorDeviceClass.DURATION,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        "input_id": 4004,
        "name": "ble rssi",
        "state_class": SensorStateClass.MEASUREMENT,
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "uom": SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    },
    {
        "input_id": 4100,
        "status_id": 4102,
        "name": "pm2_5",
        "state_class": SensorStateClass.MEASUREMENT,
        "device_class": SensorDeviceClass.PM25,
        "uom": CONCENTRATION_PARTS_PER_MILLION,
    },
    {
        "input_id": 4103,
        "status_id": 4104,
        "name": "co2",
        "state_class": SensorStateClass.MEASUREMENT,
        "device_class": SensorDeviceClass.CO2,
    },
    {
        "input_id": 4105,
        "status_id": 4106,
        "name": "voc",
        "state_class": SensorStateClass.MEASUREMENT,
        "device_class": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
        "uom": CONCENTRATION_PARTS_PER_MILLION,
    },
]

lennox_21p02_binary_sensors = [
    {"input_id": 4001, "name": "alarm_status", "entity_category": EntityCategory.DIAGNOSTIC},
    {"input_id": 4002, "name": "device_state", "entity_category": EntityCategory.DIAGNOSTIC},
    {"input_id": 4107, "name": "idle_switch", "entity_category": EntityCategory.DIAGNOSTIC},
]
