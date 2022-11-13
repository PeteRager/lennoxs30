import logging
from lennoxs30api.s30api_async import (
    lennox_system,
)
from custom_components.lennoxs30 import (
    DS_CONNECTED,
    DS_RETRY_WAIT,
    Manager,
)
import pytest
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.select import (
    EquipmentParameterSelect,
)
from homeassistant.exceptions import HomeAssistantError
from lennoxs30api.s30exception import S30Exception

from unittest.mock import patch

from tests.conftest import conftest_parameter_extra_attributes


@pytest.mark.asyncio
async def test_equipment_parameter_select_unique_id(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[130]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)
    assert c.unique_id == f"{system.unique_id()}_EPS_{equipment.equipment_id}_{parameter.pid}".replace("-", "")


@pytest.mark.asyncio
async def test_equipment_parameter_select_name(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[130]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)
    assert c.name == "South_Moetown_par_Smooth_Setback_Recovery"


@pytest.mark.asyncio
async def test_equipment_parameter_select_current_option(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[130]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)

    assert parameter.value == "1"
    assert c.current_option == "Enabled"
    assert c.available == True

    parameter.value = "0"
    assert c.current_option == "Disabled"
    assert c.available == True

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        parameter.value = "2"
        assert c.current_option == None
        assert c.available == True
        assert len(caplog.records) == 1
        assert "EquipmentParameterSelect unable to find current radio option value" in caplog.messages[0]
        assert parameter.value in caplog.messages[0]
        assert str(parameter.pid) in caplog.messages[0]
        assert "Enabled" in caplog.messages[0]
        assert "Disabled" in caplog.messages[0]


@pytest.mark.asyncio
async def test_equipment_parameter_select_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[130]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        system.executeOnUpdateCallbacksEqParameters("0_130")
        assert update_callback.call_count == 1
        assert c.available == True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_RETRY_WAIT)
        assert update_callback.call_count == 1
        assert c.available == False

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_CONNECTED)
        assert update_callback.call_count == 1
        assert c.available == True
        system.attr_updater({"status": "online"}, "status", "cloud_status")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 2
        assert c.available == True
        system.attr_updater({"status": "offline"}, "status", "cloud_status")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 3
        assert c.available == False


@pytest.mark.asyncio
async def test_equipment_parameter_select_options(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[130]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)

    opt = c.options
    assert len(opt) == 2
    assert "Enabled" in opt
    assert "Disabled" in opt


@pytest.mark.asyncio
async def test_equipment_parameter_select_async_select_options(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[130]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)

    with patch.object(system, "set_equipment_parameter_value") as set_equipment_parameter_value:
        await c.async_select_option("Enabled")
        assert set_equipment_parameter_value.call_count == 1
        assert set_equipment_parameter_value.await_args[0][0] == equipment.equipment_id
        assert set_equipment_parameter_value.await_args[0][1] == parameter.pid
        assert set_equipment_parameter_value.await_args[0][2] == "Enabled"

    manager.parameter_safety_turn_on(system.sysId)
    with patch.object(system, "set_equipment_parameter_value") as set_equipment_parameter_value:
        ex: HomeAssistantError = None
        try:
            await c.async_select_option("Enabled")
        except HomeAssistantError as e:
            ex = e
        assert ex != None
        assert set_equipment_parameter_value.call_count == 0
        s = str(ex)
        assert "Unable to set parameter" in s
        assert c._myname in s
        assert "safety switch is on" in s

    manager.parameter_safety_turn_off(system.sysId)
    with patch.object(system, "set_equipment_parameter_value") as set_equipment_parameter_value:
        await c.async_select_option("Enabled")
        assert set_equipment_parameter_value.call_count == 1
        assert set_equipment_parameter_value.await_args[0][0] == equipment.equipment_id
        assert set_equipment_parameter_value.await_args[0][1] == parameter.pid
        assert set_equipment_parameter_value.await_args[0][2] == "Enabled"

    with caplog.at_level(logging.ERROR):
        with patch.object(system, "set_equipment_parameter_value") as set_equipment_parameter_value:
            caplog.clear()
            set_equipment_parameter_value.side_effect = S30Exception("This is the error", 100, 200)
            await c.async_select_option(101)
            assert len(caplog.records) == 1
            assert "EquipmentParameterSelect::async_select_option" in caplog.messages[0]
            assert "This is the error" in caplog.messages[0]
            assert "101" in caplog.messages[0]

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(system, "set_equipment_parameter_value") as set_equipment_parameter_value:
            set_equipment_parameter_value.side_effect = S30Exception("This is the error", 10, 101)
            await c.async_select_option("bad_value")
            assert set_equipment_parameter_value.call_count == 1
            assert len(caplog.records) == 1
            msg = caplog.messages[0]
            assert "bad_value" in msg
            assert "This is the error" in msg
            assert str(equipment.equipment_id) in msg
            assert str(parameter.pid) in msg
            assert c.name in msg

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(system, "set_equipment_parameter_value") as set_equipment_parameter_value:
            set_equipment_parameter_value.side_effect = ValueError("This is the error")
            await c.async_select_option("bad_value")
            assert set_equipment_parameter_value.call_count == 1
            assert len(caplog.records) == 1
            msg = caplog.messages[0]
            assert "bad_value" in msg
            assert "This is the error" in msg
            assert "unexpected" in msg
            assert str(equipment.equipment_id) in msg
            assert str(parameter.pid) in msg
            assert c.name in msg


@pytest.mark.asyncio
async def test_equipment_parameter_select_device_info(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    await manager.create_devices()
    equipment = system.equipment[0]
    parameter = equipment.parameters[130]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id()

    equipment = system.equipment[2]
    parameter = equipment.parameters[34]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id() + "_iu"


def test_equipment_parameter_select_entity_category(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[72]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)
    assert c.entity_category == "config"


def test_equipment_parameter_select_extra_attributes(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[72]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)
    ex = c.extra_state_attributes
    conftest_parameter_extra_attributes(ex, equipment, parameter)
