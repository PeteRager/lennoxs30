# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=line-too-long

from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import PERCENTAGE
from lennoxs30api.s30api_async import lennox_system

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import LENNOX_DOMAIN, MANAGER
from custom_components.lennoxs30.sensor import async_setup_entry
from custom_components.lennoxs30.sensor_reminder import S30ReminderSensor
from tests.conftest import conftest_base_entity_availability, loadfile


@pytest.mark.asyncio()
async def test_reminder_sensor(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    system.processMessage(loadfile("reminders.json", system.sysId))

    s = S30ReminderSensor(hass, manager, system, system.reminders[0])
    assert s.unique_id == (system.unique_id + "_REMINDER_0").replace("-", "")
    assert s.available is True
    assert s.should_poll is False
    assert s.update() is True
    assert s.name == system.name + "_reminder_filter1"
    assert s.entity_registry_enabled_default is True
    assert s.native_value == 100
    assert s.native_unit_of_measurement == PERCENTAGE
    assert s.state_class == SensorStateClass.MEASUREMENT
    attrs = s.extra_state_attributes
    assert len(attrs) == 10
    assert attrs["kind"] == "filter1"
    assert attrs["enabled"] is True
    assert attrs["expired"] is False
    assert attrs["expiry_type"] == "systemRunTime"
    assert attrs["reminder_time"] == 15724800
    # Run time reminder: run time left is estimated, the counter positions are not times
    assert attrs["remaining_runtime"] == 4368
    assert attrs["set_time"] is None
    assert attrs["expiry_time"] is None
    assert attrs["expired_time"] is None
    assert attrs["viewed"] is False
    # Only enabled and expired are recorded
    assert set(attrs) - s._unrecorded_attributes == {"enabled", "expired"}  # pylint: disable=protected-access

    identifiers = s.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id

    # Reminders not configured on the thermostat are disabled and have no value
    s = S30ReminderSensor(hass, manager, system, system.reminders[2])
    assert s.name == system.name + "_reminder_uvBulb"
    assert s.entity_registry_enabled_default is False
    assert s.native_value is None

    s = S30ReminderSensor(hass, manager, system, system.reminders[7])
    assert s.native_value is None


@pytest.mark.asyncio()
async def test_reminder_sensor_calendar_times(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    # Captured from an S30 after enabling filter2 as a 91 day calendar reminder
    system.processMessage(loadfile("reminders_calendar.json", system.sysId))
    s = S30ReminderSensor(hass, manager, system, system.reminders[1])
    attrs = s.extra_state_attributes
    assert attrs["expiry_type"] == "systemCalendarTime"
    # Interval stays in seconds, times are UTC timestamps, 0 is not set
    assert attrs["reminder_time"] == 7862400
    assert attrs["set_time"] == datetime(2026, 10, 25, 1, 50, 20, tzinfo=UTC)
    assert attrs["expiry_time"] == datetime(2027, 1, 24, 1, 50, 20, tzinfo=UTC)
    assert attrs["expired_time"] is None
    assert attrs["remaining_runtime"] is None
    assert s.native_value == 100


@pytest.mark.asyncio()
async def test_reminder_sensor_subscription(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    system.processMessage(loadfile("reminders.json", system.sysId))
    s = S30ReminderSensor(hass, manager, system, system.reminders[0])
    await s.async_added_to_hass()

    message = {
        "SenderID": system.sysId,
        "MessageType": "PropertyChange",
        "Data": {"reminders": [{"id": 0, "status": {"reminderRemainingPct": 0, "reminderExpired": True}}]},
    }
    with patch.object(s, "schedule_update_ha_state") as update_callback:
        system.processMessage(message)
        assert update_callback.call_count == 1
        assert s.native_value == 0
        assert s.extra_state_attributes["expired"] is True
        assert s.extra_state_attributes["remaining_runtime"] == 0

    message["Data"]["reminders"][0] = {"id": 0, "status": {"reminderRemainingPct": 40, "reminderExpired": False}}
    with patch.object(s, "schedule_update_ha_state") as update_callback:
        system.processMessage(message)
        assert update_callback.call_count == 1
        assert s.native_value == 40
        assert s.extra_state_attributes["remaining_runtime"] == 1747

    # Another reminder changing does not update this one
    message["Data"]["reminders"][0]["id"] = 2
    with patch.object(s, "schedule_update_ha_state") as update_callback:
        system.processMessage(message)
        assert update_callback.call_count == 0

    conftest_base_entity_availability(manager, system, s)


@pytest.mark.asyncio()
async def test_reminder_sensor_setup(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    entry = manager.config_entry
    hass.data["lennoxs30"] = {}
    hass.data["lennoxs30"][entry.unique_id] = {MANAGER: manager}
    manager.create_inverter_power = False
    manager.create_sensors = False
    manager.create_diagnostic_sensors = False
    manager.create_alert_sensors = False
    manager.api.isLANConnection = False
    system.processMessage(loadfile("reminders.json", system.sysId))

    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    sensor_list = [x for x in async_add_entities.call_args[0][0] if isinstance(x, S30ReminderSensor)]
    assert len(sensor_list) == 8
    assert [x.name for x in sensor_list if x.entity_registry_enabled_default] == [system.name + "_reminder_filter1"]
