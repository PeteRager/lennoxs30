from lennoxs30api.s30api_async import (
    LENNOX_HUMIDITY_MODE_OFF,
    LENNOX_HUMIDITY_MODE_HUMIDIFY,
    LENNOX_HUMIDITY_MODE_DEHUMIDIFY,
    lennox_system,
    lennox_zone,
)
from custom_components.lennoxs30 import (
    Manager,
)
import pytest

from custom_components.lennoxs30.select import (
    HumidityModeSelect,
)

from unittest.mock import patch


@pytest.mark.asyncio
async def test_humidity_mode_select_unique_id(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    zone: lennox_zone = system._zoneList[0]
    c = HumidityModeSelect(hass, manager, system, zone)

    assert c.unique_id == zone.unique_id + "_HMS"


@pytest.mark.asyncio
async def test_humidity_mode_select_name(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    zone: lennox_zone = system._zoneList[0]
    c = HumidityModeSelect(hass, manager, system, zone)

    assert c.name == system.name + "_" + zone.name + "_humidity_mode"


@pytest.mark.asyncio
async def test_humidity_mode_select_current_option(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    zone: lennox_zone = system._zoneList[0]

    c = HumidityModeSelect(hass, manager, system, zone)
    assert c.current_option == LENNOX_HUMIDITY_MODE_OFF

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        zone.humidityMode = LENNOX_HUMIDITY_MODE_DEHUMIDIFY
        c.zone_update_callback()
        assert c.current_option == LENNOX_HUMIDITY_MODE_DEHUMIDIFY

        zone.humidityMode = LENNOX_HUMIDITY_MODE_HUMIDIFY
        c.zone_update_callback()
        assert c.current_option == LENNOX_HUMIDITY_MODE_HUMIDIFY


@pytest.mark.asyncio
async def test_humidity_mode_select_options(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    zone: lennox_zone = system._zoneList[0]
    c = HumidityModeSelect(hass, manager, system, zone)

    opt = c.options
    assert len(opt) == 2
    assert LENNOX_HUMIDITY_MODE_OFF in opt
    assert LENNOX_HUMIDITY_MODE_DEHUMIDIFY in opt
    assert zone.dehumidificationOption == True
    assert zone.humidificationOption == False

    zone.humidificationOption = True
    opt = c.options
    assert len(opt) == 3
    assert LENNOX_HUMIDITY_MODE_OFF in opt
    assert LENNOX_HUMIDITY_MODE_DEHUMIDIFY in opt
    assert LENNOX_HUMIDITY_MODE_HUMIDIFY in opt
    assert zone.dehumidificationOption == True

    zone.humidificationOption = False
    zone.dehumidificationOption = False
    opt = c.options
    assert len(opt) == 1
    assert LENNOX_HUMIDITY_MODE_OFF in opt


@pytest.mark.asyncio
async def test_humidity_mode_select_async_select_options(
    hass, manager: Manager, caplog
):
    system: lennox_system = manager._api._systemList[0]
    zone: lennox_zone = system._zoneList[0]
    c = HumidityModeSelect(hass, manager, system, zone)

    with patch.object(zone, "setHumidityMode") as set_humidity_mode:
        await c.async_select_option(LENNOX_HUMIDITY_MODE_OFF)
        assert set_humidity_mode.call_count == 1
        arg0 = set_humidity_mode.await_args[0][0]
        assert arg0 == LENNOX_HUMIDITY_MODE_OFF

    with patch.object(zone, "setHumidityMode") as set_humidity_mode:
        await c.async_select_option(LENNOX_HUMIDITY_MODE_DEHUMIDIFY)
        assert set_humidity_mode.call_count == 1
        arg0 = set_humidity_mode.await_args[0][0]
        assert arg0 == LENNOX_HUMIDITY_MODE_DEHUMIDIFY

    with patch.object(zone, "setHumidityMode") as set_humidity_mode:
        await c.async_select_option(LENNOX_HUMIDITY_MODE_HUMIDIFY)
        assert set_humidity_mode.call_count == 1
        arg0 = set_humidity_mode.await_args[0][0]
        assert arg0 == LENNOX_HUMIDITY_MODE_HUMIDIFY
