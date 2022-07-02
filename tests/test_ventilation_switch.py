from lennoxs30api.s30api_async import (
    lennox_system,
)
from custom_components.lennoxs30 import (
    DS_RETRY_WAIT,
    Manager,
)

from custom_components.lennoxs30.const import LENNOX_DOMAIN

import pytest
from custom_components.lennoxs30.switch import (
    S30VentilationSwitch,
)

from unittest.mock import patch


@pytest.mark.asyncio
async def test_ventilation_switch(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = S30VentilationSwitch(hass, manager, system)

    assert c.unique_id == (system.unique_id() + "_VST").replace("-", "")
    assert c.name == system.name + "_ventilation"

    attrs = c.extra_state_attributes
    assert len(attrs) == 3
    assert attrs["ventilationRemainingTime"] == system.ventilationRemainingTime
    assert attrs["ventilatingUntilTime"] == system.ventilatingUntilTime
    assert attrs["diagVentilationRuntime"] == system.diagVentilationRuntime

    assert c.update() == True
    assert c.should_poll == False
    assert c.available == True

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id()

    system.ventilationMode = "on"
    assert c.is_on == True

    system.ventilationMode = "off"
    assert c.is_on == False

    with patch.object(system, "ventilation_on") as ventilation_on:
        await c.async_turn_on()
        assert ventilation_on.call_count == 1

    with patch.object(system, "ventilation_off") as ventilation_off:
        await c.async_turn_off()
        assert ventilation_off.call_count == 1


@pytest.mark.asyncio
async def test_ventilation_switch_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
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

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_RETRY_WAIT)
        assert update_callback.call_count == 1
        assert c.available == False
