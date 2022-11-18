from lennoxs30api.s30api_async import lennox_system, LENNOX_VENTILATION_DAMPER
from custom_components.lennoxs30 import (
    Manager,
)

from custom_components.lennoxs30.const import LENNOX_DOMAIN

import pytest
from custom_components.lennoxs30.switch import (
    S30VentilationSwitch,
)

from unittest.mock import patch

from tests.conftest import conftest_base_entity_availability


@pytest.mark.asyncio
async def test_ventilation_switch(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    system.ventilationUnitType = LENNOX_VENTILATION_DAMPER
    c = S30VentilationSwitch(hass, manager, system)

    assert c.unique_id == (system.unique_id + "_VST").replace("-", "")
    assert c.name == system.name + "_ventilation"

    attrs = c.extra_state_attributes
    assert len(attrs) == 5
    assert attrs["ventilationRemainingTime"] == system.ventilationRemainingTime
    assert attrs["ventilatingUntilTime"] == system.ventilatingUntilTime
    assert attrs["diagVentilationRuntime"] == system.diagVentilationRuntime
    assert attrs["alwaysOn"] == False
    assert attrs["timed"] == False

    assert c.update() == True
    assert c.should_poll == False
    assert c.available == True

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id

    system.ventilationRemainingTime = 0
    system.ventilationMode = "on"
    assert c.is_on == True
    attrs = c.extra_state_attributes
    assert len(attrs) == 5
    assert attrs["ventilationRemainingTime"] == system.ventilationRemainingTime
    assert attrs["ventilatingUntilTime"] == system.ventilatingUntilTime
    assert attrs["diagVentilationRuntime"] == system.diagVentilationRuntime
    assert attrs["alwaysOn"] == True
    assert attrs["timed"] == False

    system.ventilationMode = "off"
    assert c.is_on == False
    attrs = c.extra_state_attributes
    assert len(attrs) == 5
    assert attrs["ventilationRemainingTime"] == system.ventilationRemainingTime
    assert attrs["ventilatingUntilTime"] == system.ventilatingUntilTime
    assert attrs["diagVentilationRuntime"] == system.diagVentilationRuntime
    assert attrs["alwaysOn"] == False
    assert attrs["timed"] == False

    system.ventilationMode = "on"
    with patch.object(system, "ventilation_on") as ventilation_on:
        await c.async_turn_on()
        assert ventilation_on.call_count == 1

    with patch.object(system, "ventilation_off") as ventilation_off:
        with patch.object(system, "ventilation_timed") as ventilation_timed:
            await c.async_turn_off()
            assert ventilation_off.call_count == 1
            assert ventilation_timed.call_count == 0

    system.ventilationMode = "off"
    with patch.object(system, "ventilation_off") as ventilation_off:
        with patch.object(system, "ventilation_timed") as ventilation_timed:
            await c.async_turn_off()
            assert ventilation_off.call_count == 0
            assert ventilation_timed.call_count == 0

    system.ventilationRemainingTime = 100
    assert c.is_on == True
    attrs = c.extra_state_attributes
    assert len(attrs) == 5
    assert attrs["ventilationRemainingTime"] == 100
    assert attrs["ventilatingUntilTime"] == system.ventilatingUntilTime
    assert attrs["diagVentilationRuntime"] == system.diagVentilationRuntime
    assert attrs["alwaysOn"] == False
    assert attrs["timed"] == True

    with patch.object(system, "ventilation_on") as ventilation_on:
        await c.async_turn_on()
        assert ventilation_on.call_count == 1

    with patch.object(system, "ventilation_off") as ventilation_off:
        with patch.object(system, "ventilation_timed") as ventilation_timed:
            await c.async_turn_off()
            assert ventilation_off.call_count == 0
            assert ventilation_timed.call_count == 1
            assert ventilation_timed.call_args[0][0] == 0

    system.ventilationMode = "on"
    with patch.object(system, "ventilation_off") as ventilation_off:
        with patch.object(system, "ventilation_timed") as ventilation_timed:
            await c.async_turn_off()
            assert ventilation_off.call_count == 1
            assert ventilation_timed.call_count == 1
            assert ventilation_timed.call_args[0][0] == 0


@pytest.mark.asyncio
async def test_ventilation_switch_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = S30VentilationSwitch(hass, manager, system)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        vent = "off" if system.ventilationMode == "on" else "off"
        set = {"ventilationMode": vent}
        system.attr_updater(set, "ventilationMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        if vent == "off":
            assert c.is_on == False
        else:
            assert c.is_on == True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {"ventilationRemainingTime": 12345}
        system.attr_updater(set, "ventilationRemainingTime")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        attrs = c.extra_state_attributes
        assert attrs["ventilationRemainingTime"] == 12345

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {"ventilatingUntilTime": 1234}
        system.attr_updater(set, "ventilatingUntilTime")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        attrs = c.extra_state_attributes
        assert attrs["ventilatingUntilTime"] == 1234

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {"diagVentilationRuntime": 9191}
        system.attr_updater(set, "diagVentilationRuntime")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        attrs = c.extra_state_attributes
        assert attrs["diagVentilationRuntime"] == 9191

    conftest_base_entity_availability(manager, system, c)
