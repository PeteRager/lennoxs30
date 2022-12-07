# pylint: disable=too-many-lines
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

from unittest.mock import patch
import pytest

from homeassistant.const import TEMP_FAHRENHEIT
from homeassistant.exceptions import HomeAssistantError

from lennoxs30api.s30api_async import lennox_system

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import (
    LENNOX_DOMAIN,
    UNIQUE_ID_SUFFIX_EQ_PARAM_NUMBER,
)
from custom_components.lennoxs30.number import (
    EquipmentParameterNumber,
)

from tests.conftest import (
    conf_test_exception_handling,
    conftest_base_entity_availability,
    conftest_parameter_extra_attributes,
)


@pytest.mark.asyncio
async def test_equipment_parameter_number_unique_id(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[72]
    c = EquipmentParameterNumber(hass, manager, system, equipment, parameter)
    assert c.unique_id == (f"{system.unique_id}_{UNIQUE_ID_SUFFIX_EQ_PARAM_NUMBER}_0_72").replace("-", "")


@pytest.mark.asyncio
async def test_equipment_parameter_number_name(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[72]
    c = EquipmentParameterNumber(hass, manager, system, equipment, parameter)
    assert c.name == f"{system.name}_par_{parameter.name}".replace(" ", "_")


@pytest.mark.asyncio
async def test_equipment_parameter_number_unit_of_measure(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[72]
    c = EquipmentParameterNumber(hass, manager, system, equipment, parameter)
    assert c.unit_of_measurement == TEMP_FAHRENHEIT


@pytest.mark.asyncio
async def test_equipment_parameter_number_max_value(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[72]
    c = EquipmentParameterNumber(hass, manager, system, equipment, parameter)
    assert c.max_value == float(parameter.range_max)


@pytest.mark.asyncio
async def test_equipment_parameter_number_min_value(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[72]
    c = EquipmentParameterNumber(hass, manager, system, equipment, parameter)
    assert c.min_value == float(parameter.range_min)


@pytest.mark.asyncio
async def test_equipment_parameter_number_step(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[72]
    c = EquipmentParameterNumber(hass, manager, system, equipment, parameter)
    assert c.step == float(parameter.range_inc)


@pytest.mark.asyncio
async def test_equipment_parameter_number_value(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[72]
    c = EquipmentParameterNumber(hass, manager, system, equipment, parameter)
    assert c.value == parameter.value


@pytest.mark.asyncio
async def test_equipment_parameter_number_set_value(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[72]
    c = EquipmentParameterNumber(hass, manager, system, equipment, parameter)

    with patch.object(system, "set_equipment_parameter_value") as set_equipment_parameter_value:
        await c.async_set_native_value(60.0)
        assert set_equipment_parameter_value.call_count == 1
        assert set_equipment_parameter_value.await_args[0][0] == equipment.equipment_id
        assert set_equipment_parameter_value.await_args[0][1] == parameter.pid
        assert set_equipment_parameter_value.await_args[0][2] == 60.0

    manager.parameter_safety_turn_on(system.sysId)
    with patch.object(system, "set_equipment_parameter_value") as set_equipment_parameter_value:
        ex: HomeAssistantError = None
        try:
            await c.async_set_native_value(60.0)
        except HomeAssistantError as e:
            ex = e
        assert ex is not None
        assert set_equipment_parameter_value.call_count == 0
        s = str(ex)
        assert "Unable to set parameter" in s
        assert c._myname in s
        assert "safety switch is on" in s

    manager.parameter_safety_turn_off(system.sysId)
    with patch.object(system, "set_equipment_parameter_value") as set_equipment_parameter_value:
        await c.async_set_native_value(60.0)
        assert set_equipment_parameter_value.call_count == 1
        assert set_equipment_parameter_value.await_args[0][0] == equipment.equipment_id
        assert set_equipment_parameter_value.await_args[0][1] == parameter.pid
        assert set_equipment_parameter_value.await_args[0][2] == 60.0

    await conf_test_exception_handling(system, "set_equipment_parameter_value", c, c.async_set_native_value, value=101)


@pytest.mark.asyncio
async def test_equipment_parameter_number_device_info(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[72]
    await manager.create_devices()
    c = EquipmentParameterNumber(hass, manager, system, equipment, parameter)
    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == manager.system_equip_device_map[system.sysId][0].unique_name


@pytest.mark.asyncio
async def test_equipment_parameter_number_subscription(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[72]
    c = EquipmentParameterNumber(hass, manager, system, equipment, parameter)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        system.executeOnUpdateCallbacksEqParameters("0_72")
        assert update_callback.call_count == 1
        assert c.available is True

    conftest_base_entity_availability(manager, system, c)


def test_equipment_parameter_number_entity_category(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[72]
    c = EquipmentParameterNumber(hass, manager, system, equipment, parameter)
    assert c.entity_category == "config"


def test_equipment_parameter_number_mode(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[72]
    c = EquipmentParameterNumber(hass, manager, system, equipment, parameter)
    assert c.mode == "box"


def test_equipment_parameter_select_extra_attributes(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[72]
    c = EquipmentParameterNumber(hass, manager, system, equipment, parameter)
    conftest_parameter_extra_attributes(c.extra_state_attributes, equipment, parameter)


@pytest.mark.asyncio
async def test_equipment_parameter_number_set_zonetest_parameter(hass, manager_system_04_furn_ac_zoning: Manager):
    manager = manager_system_04_furn_ac_zoning
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[256]
    c = EquipmentParameterNumber(hass, manager, system, equipment, parameter)

    with patch.object(system, "set_zone_test_parameter_value") as set_zone_test_parameter_value:
        await c.async_set_zonetest_parameter(60.0, True)
        assert set_zone_test_parameter_value.call_count == 1
        assert set_zone_test_parameter_value.await_args[0][0] == parameter.pid
        assert set_zone_test_parameter_value.await_args[0][1] == 60.0
        assert set_zone_test_parameter_value.await_args[0][2] is True

    with patch.object(system, "set_zone_test_parameter_value") as set_zone_test_parameter_value:
        await c.async_set_zonetest_parameter(70.0, False)
        assert set_zone_test_parameter_value.call_count == 1
        assert set_zone_test_parameter_value.await_args[0][0] == parameter.pid
        assert set_zone_test_parameter_value.await_args[0][1] == 70.0
        assert set_zone_test_parameter_value.await_args[0][2] is False

    await conf_test_exception_handling(
        system, "set_zone_test_parameter_value", c, c.async_set_zonetest_parameter, value=70.0, enabled=False
    )
