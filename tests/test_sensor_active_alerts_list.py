"""Test Sensor Alert"""
from unittest.mock import patch
import pytest

from lennoxs30api.s30api_async import (
    lennox_system,
)
from custom_components.lennoxs30 import (
    Manager,
)
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.sensor import (
    S30ActiveAlertsList,
)
from tests.conftest import conftest_base_entity_availability, loadfile


@pytest.mark.asyncio
async def test_active_alerts_sensor(hass, manager: Manager):
    """Test the alert sensor"""
    manager.is_metric = False
    system: lennox_system = manager.api.system_list[0]
    message = loadfile("alert_lockouts_2_active.json", sysId=system.sysId)
    manager.api.processMessage(message)
    sensor = S30ActiveAlertsList(hass, manager, system)

    assert sensor.unique_id == (system.unique_id + "_ACTIVE_ALERTS").replace("-", "")
    assert sensor.name == system.name + "_active_alerts"
    assert sensor.available is True
    assert sensor.should_poll is False
    assert sensor.available is True
    assert sensor.update() is True
    assert sensor.state_class == "measurement"
    assert sensor.state == 2
    attrs = sensor.extra_state_attributes
    assert len(attrs) == 4

    alert = attrs["alert_list"][0]
    assert alert["code"] == 19
    assert alert["message"] == "High Ambient Auxiliary Heat Lockout"
    assert alert["isStillActive"] is True
    assert alert["priority"] == "info"

    alert = attrs["alert_list"][1]
    assert alert["code"] == 18
    assert alert["message"] == "Low Ambient HP Heat Lockout"
    assert alert["isStillActive"] is True
    assert alert["priority"] == "info"

    assert sensor.state == system.alerts_num_active
    assert attrs["alerts_num_cleared"] == 46
    assert attrs["alerts_last_cleared_id"] == 45
    assert attrs["alerts_num_in_active_array"] == 2

    system.alerts_num_active = None
    assert sensor.state == 0

    system.alerts_num_cleared = None
    assert sensor.extra_state_attributes["alerts_num_cleared"] == 0
    system.alerts_num_cleared = 46
    system.alerts_last_cleared_id = None
    assert sensor.extra_state_attributes["alerts_last_cleared_id"] == 0
    system.alerts_last_cleared_id = 45
    system.alerts_num_in_active_array = None
    assert sensor.extra_state_attributes["alerts_num_in_active_array"] == 0

    identifiers = sensor.device_info["identifiers"]
    for ids in identifiers:
        assert ids[0] == LENNOX_DOMAIN
        assert ids[1] == system.unique_id


@pytest.mark.asyncio
async def test_active_alerts_subscription(hass, manager: Manager):
    """Test the alert sensor subscription"""
    system: lennox_system = manager.api.system_list[0]
    sensor = S30ActiveAlertsList(hass, manager, system)
    await sensor.async_added_to_hass()

    with patch.object(sensor, "schedule_update_ha_state") as update_callback:
        manager.is_metric = False
        update = {"alerts_num_active": 4}
        system.attr_updater(update, "alerts_num_active")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert sensor.state == 4

    with patch.object(sensor, "schedule_update_ha_state") as update_callback:
        manager.is_metric = False
        update = {"alerts_num_cleared": 2}
        system.attr_updater(update, "alerts_num_cleared")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert sensor.extra_state_attributes["alerts_num_cleared"] == 2

    with patch.object(sensor, "schedule_update_ha_state") as update_callback:
        manager.is_metric = False
        update = {"alerts_last_cleared_id": 19}
        system.attr_updater(update, "alerts_last_cleared_id")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert sensor.extra_state_attributes["alerts_last_cleared_id"] == 19

    with patch.object(sensor, "schedule_update_ha_state") as update_callback:
        update = {"alerts_last_cleared_id": 19}
        message = loadfile("alert_lockouts_2_active.json", sysId=system.sysId)
        manager.api.processMessage(message)
        assert update_callback.call_count == 1
        assert len(sensor.extra_state_attributes["alert_list"]) == 2

    conftest_base_entity_availability(manager, system, sensor)
