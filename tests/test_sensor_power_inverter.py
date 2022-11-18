from distutils.log import warn
import logging
from lennoxs30api.s30api_async import (
    LENNOX_STATUS_NOT_EXIST,
    LENNOX_STATUS_GOOD,
    LENNOX_STATUS_NOT_AVAILABLE,
    lennox_system,
    lennox_zone,
)
from custom_components.lennoxs30 import (
    Manager,
)
import pytest
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.sensor import (
    S30InverterPowerSensor,
)

from homeassistant.const import TEMP_CELSIUS, POWER_WATT, DEVICE_CLASS_POWER

from homeassistant.components.sensor import (
    STATE_CLASS_MEASUREMENT,
)


from unittest.mock import patch

from tests.conftest import conftest_base_entity_availability


@pytest.mark.asyncio
async def test_power_inverter_sensor(hass, manager: Manager, caplog):
    manager.is_metric = False
    system: lennox_system = manager.api.system_list[0]
    system.diagLevel = 2
    s = S30InverterPowerSensor(hass, manager, system)

    assert s.unique_id == (system.unique_id + "_IE").replace("-", "")
    assert s.name == system.name + "_inverter_energy"
    assert s.available == True
    assert s.should_poll == False
    assert s.available == True
    assert s.update() == True
    assert len(s.extra_state_attributes) == 0

    system.diagInverterInputCurrent = None
    system.diagInverterInputVoltage = None
    assert s.state == None
    system.diagInverterInputVoltage = 240
    assert s.state == None
    system.diagInverterInputCurrent = 10
    assert s.state == 2400

    system.diagInverterInputVoltage = "waiting..."
    assert s.state == None
    system.diagInverterInputVoltage = 240
    system.diagInverterInputCurrent = "waiting..."
    assert s.state == None

    with caplog.at_level(logging.WARNING):
        caplog.clear()
        system.diagInverterInputVoltage = "NAN"
        system.diagInverterInputCurrent = 10
        assert s.state == None
        assert len(caplog.records) == 1
        assert "NAN" in caplog.messages[0]

    assert s.unit_of_measurement == POWER_WATT

    assert s.device_class == DEVICE_CLASS_POWER
    assert s.state_class == STATE_CLASS_MEASUREMENT

    identifiers = s.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id + "_ou"


@pytest.mark.asyncio
async def test_power_inverter_sensor_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    system.diagLevel = 2
    s = S30InverterPowerSensor(hass, manager, system)
    await s.async_added_to_hass()

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        manager.is_metric = False
        set = {"diagInverterInputVoltage": 240.5}
        system.attr_updater(set, "diagInverterInputVoltage")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        manager.is_metric = False
        set = {"diagInverterInputCurrent": 13.4}
        system.attr_updater(set, "diagInverterInputCurrent")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    conftest_base_entity_availability(manager, system, s)

    with patch.object(s, "schedule_update_ha_state") as s_update_callback:
        set = {"diagLevel": 0}
        system.attr_updater(set, "diagLevel")
        system.executeOnUpdateCallbacks()
        assert s_update_callback.call_count == 1
        assert s.available == False

    with patch.object(s, "schedule_update_ha_state") as s_update_callback:
        system.attr_updater({"status": "online"}, "status", "cloud_status")
        system.executeOnUpdateCallbacks()
        assert s_update_callback.call_count == 1
        set = {"diagLevel": 2}
        system.attr_updater(set, "diagLevel")
        system.executeOnUpdateCallbacks()
        assert s_update_callback.call_count == 2
        assert s.available == True
