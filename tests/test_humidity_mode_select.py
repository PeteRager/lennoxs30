# pylint: disable=too-many-lines
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

import logging
from unittest.mock import patch
import pytest

from homeassistant.exceptions import HomeAssistantError

from lennoxs30api.s30api_async import (
    LENNOX_HUMIDITY_MODE_OFF,
    LENNOX_HUMIDITY_MODE_HUMIDIFY,
    LENNOX_HUMIDITY_MODE_DEHUMIDIFY,
    lennox_system,
    lennox_zone,
    LENNOX_ZONING_MODE_CENTRAL,
)

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.select import HumidityModeSelect
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from tests.conftest import (
    conf_test_exception_handling,
    conftest_base_entity_availability,
    conf_test_select_info_async_select_option,
)


@pytest.mark.asyncio
async def test_humidity_mode_select_unique_id(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = HumidityModeSelect(hass, manager, system, zone)

    assert c.unique_id == zone.unique_id + "_HMS"


@pytest.mark.asyncio
async def test_humidity_mode_select_name(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = HumidityModeSelect(hass, manager, system, zone)

    assert c.name == system.name + "_" + zone.name + "_humidity_mode"


@pytest.mark.asyncio
async def test_humidity_mode_select_current_option(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]

    c = HumidityModeSelect(hass, manager, system, zone)
    with patch.object(c, "schedule_update_ha_state") as _:
        assert c.current_option == LENNOX_HUMIDITY_MODE_OFF

        zone.humidityMode = LENNOX_HUMIDITY_MODE_DEHUMIDIFY
        c.zone_update_callback()
        assert c.current_option == LENNOX_HUMIDITY_MODE_DEHUMIDIFY

        zone.humidityMode = LENNOX_HUMIDITY_MODE_HUMIDIFY
        c.zone_update_callback()
        assert c.current_option == LENNOX_HUMIDITY_MODE_HUMIDIFY

        system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
        assert c.current_option == LENNOX_HUMIDITY_MODE_HUMIDIFY


@pytest.mark.asyncio
async def test_humidity_mode_select_current_option_z1(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[1]

    c = HumidityModeSelect(hass, manager, system, zone)
    await c.async_added_to_hass()
    c.entity_id = "select.my_select_zone_1"
    assert c.current_option == LENNOX_HUMIDITY_MODE_OFF
    assert c.available is True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        zone.humidityMode = None
        update_set = {"humidityMode": LENNOX_HUMIDITY_MODE_DEHUMIDIFY}
        zone.attr_updater(update_set, "humidityMode")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option == LENNOX_HUMIDITY_MODE_DEHUMIDIFY
        assert c.available is True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {"humidityMode": LENNOX_HUMIDITY_MODE_HUMIDIFY}
        zone.attr_updater(update_set, "humidityMode")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option == LENNOX_HUMIDITY_MODE_HUMIDIFY
        assert c.available is True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {"humidityMode": LENNOX_HUMIDITY_MODE_DEHUMIDIFY}
        zone.attr_updater(update_set, "humidityMode")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option == LENNOX_HUMIDITY_MODE_DEHUMIDIFY

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {"zoningMode": LENNOX_ZONING_MODE_CENTRAL}
        system.attr_updater(update_set, "zoningMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option is None
        assert c.available is True

    conftest_base_entity_availability(manager, system, c)


@pytest.mark.asyncio
async def test_humidity_mode_select_options(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = HumidityModeSelect(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = HumidityModeSelect(hass, manager, system, zone1)
    c1.entity_id = "select.my_select_zone_1"

    opt = c.options
    assert len(opt) == 2
    assert LENNOX_HUMIDITY_MODE_OFF in opt
    assert LENNOX_HUMIDITY_MODE_DEHUMIDIFY in opt
    assert zone.dehumidificationOption is True
    assert zone.humidificationOption is False

    zone.humidificationOption = True
    opt = c.options
    assert len(opt) == 3
    assert LENNOX_HUMIDITY_MODE_OFF in opt
    assert LENNOX_HUMIDITY_MODE_DEHUMIDIFY in opt
    assert LENNOX_HUMIDITY_MODE_HUMIDIFY in opt
    assert zone.dehumidificationOption is True

    zone.humidificationOption = False
    zone.dehumidificationOption = False
    opt = c.options
    assert len(opt) == 1
    assert LENNOX_HUMIDITY_MODE_OFF in opt

    opt = c1.options
    assert len(opt) == 2
    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    opt = c.options
    assert len(opt) == 1
    assert LENNOX_HUMIDITY_MODE_OFF in opt
    opt = c1.options
    assert len(opt) == 0


@pytest.mark.asyncio
async def test_humidity_mode_select_async_select_options(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = HumidityModeSelect(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = HumidityModeSelect(hass, manager, system, zone1)
    c1.entity_id = "select.my_select_zone_1"

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

    await conf_test_exception_handling(
        zone, "setHumidityMode", c, c.async_select_option, option=LENNOX_HUMIDITY_MODE_HUMIDIFY
    )

    await conf_test_select_info_async_select_option(system, "setHumidityMode", c, caplog)

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(zone1, "setHumidityMode") as set_humidity_mode:
            ex: HomeAssistantError = None
            try:
                await c1.async_select_option(LENNOX_HUMIDITY_MODE_DEHUMIDIFY)
            except HomeAssistantError as err:
                ex = err
            assert ex is not None
            assert set_humidity_mode.call_count == 0
            assert "disabled" in str(ex)


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_device_info(hass, manager_mz: Manager):
    manager = manager_mz
    await manager.create_devices()
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = HumidityModeSelect(hass, manager, system, zone)

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == zone.unique_id
