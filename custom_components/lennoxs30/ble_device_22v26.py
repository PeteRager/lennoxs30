"""Lennox BLE Repeater."""

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import SIGNAL_STRENGTH_DECIBELS_MILLIWATT, UnitOfTime
from homeassistant.helpers.entity import EntityCategory

lennox_22v26_sensors = [
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
        # The repeater reports this input with unit "none"
        "uom": UnitOfTime.SECONDS,
    },
    {
        "input_id": 4004,
        "name": "ble rssi",
        "state_class": SensorStateClass.MEASUREMENT,
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "uom": SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    },
]

lennox_22v26_binary_sensors = [
    {"input_id": 4001, "name": "alarm_status", "entity_category": EntityCategory.DIAGNOSTIC},
    {"input_id": 4002, "name": "device_state", "entity_category": EntityCategory.DIAGNOSTIC},
]
