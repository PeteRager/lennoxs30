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
    S30AlertSensor,
)
from tests.conftest import conftest_base_entity_availability


@pytest.mark.asyncio
async def test_alert_sensor(hass, manager: Manager):
    """Test the alert sensor"""
    manager.is_metric = False
    system: lennox_system = manager.api.system_list[0]
    sensor = S30AlertSensor(hass, manager, system)

    assert sensor.unique_id == (system.unique_id + "_ALERT").replace("-", "")
    assert sensor.name == system.name + "_alert"
    assert sensor.available is True
    assert sensor.should_poll is False
    assert sensor.available is True
    assert sensor.update() is True
    assert sensor.state_class is None
    assert len(sensor.extra_state_attributes) == 0

    assert sensor.state == system.alert

    identifiers = sensor.device_info["identifiers"]
    for ids in identifiers:
        assert ids[0] == LENNOX_DOMAIN
        assert ids[1] == system.unique_id


@pytest.mark.asyncio
async def test_alert_subscription(hass, manager: Manager):
    """Test the alert sensor subscription"""
    system: lennox_system = manager.api.system_list[0]
    sensor = S30AlertSensor(hass, manager, system)
    await sensor.async_added_to_hass()

    with patch.object(sensor, "schedule_update_ha_state") as update_callback:
        manager.is_metric = False
        update = {"alert": "critical"}
        system.attr_updater(update, "alert")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert sensor.state == "critical"

    conftest_base_entity_availability(manager, system, sensor)
