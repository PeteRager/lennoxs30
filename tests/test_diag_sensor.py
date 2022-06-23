from lennoxs30api.s30api_async import (
    lennox_system,
)
from custom_components.lennoxs30 import (
    Manager,
)
import pytest
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.sensor import (
    S30DiagSensor,
)

from homeassistant.const import (
    PERCENTAGE,
    TEMP_FAHRENHEIT,
    FREQUENCY_HERTZ,
    ELECTRIC_CURRENT_AMPERE,
    VOLUME_FLOW_RATE_CUBIC_FEET_PER_MINUTE,
    ELECTRIC_POTENTIAL_VOLT,
    TIME_MINUTES,
)

from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT, SensorDeviceClass

from homeassistant.helpers.entity import EntityCategory

from unittest.mock import patch

from tests.conftest import loadfile


@pytest.mark.asyncio
async def test_diag_sensor_state(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[0]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.state == "No"
    assert s.extra_state_attributes == {}
    assert s.update() == True
    assert s.should_poll == False
    assert s.name == "Comp. Short Cycle Delay Active"
    assert s.state_class == STATE_CLASS_MEASUREMENT
    assert s.entity_category == EntityCategory.DIAGNOSTIC


@pytest.mark.asyncio
async def test_diag_sensor_async_added_to_hass(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[0]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    await s.async_added_to_hass()
    assert len(system._diagcallbacks) == 1
    assert system._diagcallbacks[0]["func"] == s.update_callback
    assert system._diagcallbacks[0]["match"] == ["1_0"]


@pytest.mark.asyncio
async def test_diag_sensor_update_callback(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[0]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    await s.async_added_to_hass()
    assert s.state == "No"

    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[1]
    s1 = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    await s1.async_added_to_hass()
    assert s1.state == "0.0"

    api = manager._api
    data = loadfile("equipments_diag_update.json", system.sysId)

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        api.processMessage(data)
        assert update_callback.call_count == 1
    assert s.state == "Yes"
    assert s1.state == "10.0"


@pytest.mark.asyncio
async def test_diag_sensor_unique_id(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[0]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    st = f"{system.unique_id()}_DS_1_Comp. Short Cycle Delay Active".replace("-", "")
    assert s.unique_id == st


@pytest.mark.asyncio
async def test_diag_sensor_unit_of_measure_device_class(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[0]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement == None
    assert s.device_class == None

    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[1]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement == PERCENTAGE
    assert s.device_class == None

    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[9]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement == TEMP_FAHRENHEIT
    assert s.device_class == SensorDeviceClass.TEMPERATURE

    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[12]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement == TIME_MINUTES
    assert s.device_class == None

    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[16]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement == FREQUENCY_HERTZ
    assert s.device_class == SensorDeviceClass.FREQUENCY

    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[20]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement == ELECTRIC_CURRENT_AMPERE
    assert s.device_class == SensorDeviceClass.CURRENT

    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[21]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement == ELECTRIC_POTENTIAL_VOLT
    assert s.device_class == SensorDeviceClass.VOLTAGE

    equipment = system.equipment[2]
    diagnostic = equipment.diagnostics[1]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement == VOLUME_FLOW_RATE_CUBIC_FEET_PER_MINUTE
    assert s.device_class == None


@pytest.mark.asyncio
async def test_diag_sensor_device_info(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[0]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)

    identifiers = s.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id() + "_ou"

    equipment = system.equipment[2]
    diagnostic = equipment.diagnostics[1]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement == VOLUME_FLOW_RATE_CUBIC_FEET_PER_MINUTE
    assert s.device_class == None

    identifiers = s.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id() + "_iu"
