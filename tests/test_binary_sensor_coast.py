"""Test the coasting binary sensor"""
# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring

from unittest.mock import Mock, patch

import pytest
from lennoxs30api.s30api_async import (
    LENNOX_ZONING_MODE_CENTRAL,
    LENNOX_ZONING_MODE_ZONED,
    lennox_system,
)

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.binary_sensor import (
    S30CoastBinarySensor,
    async_setup_entry,
)
from custom_components.lennoxs30.const import (
    LENNOX_DOMAIN,
    MANAGER,
    UNIQUE_ID_SUFFIX_COAST_SENSOR,
)
from tests.conftest import conftest_base_entity_availability


@pytest.mark.asyncio()
async def test_coast_init(hass, manager: Manager):
    """Test the binary sensor"""
    system: lennox_system = manager.api.system_list[0]
    zone = system.zone_list[0]
    sensor = S30CoastBinarySensor(hass, manager, system, zone)
    assert sensor.unique_id == ((system.unique_id + "_" + str(zone.id)).replace("-", "") + UNIQUE_ID_SUFFIX_COAST_SENSOR)
    assert sensor.update() is True
    assert sensor.should_poll is False
    assert sensor.name == system.name + "_" + zone.name + "_coasting"

    # No coast flags received from the panel yet
    zone.heatCoast = None
    zone.coolCoast = None
    assert sensor.available is False

    zone.heatCoast = False
    zone.coolCoast = False
    assert sensor.available is True
    assert sensor.state == "off"
    assert sensor.is_on is False
    assert sensor.extra_state_attributes == {"heatCoast": False, "coolCoast": False}

    # Heat coast, then cool coast
    zone.heatCoast = True
    assert sensor.state == "on"
    assert sensor.is_on is True
    zone.heatCoast = False
    zone.coolCoast = True
    assert sensor.state == "on"
    assert sensor.is_on is True

    identifiers = sensor.device_info["identifiers"]
    for ids in identifiers:
        assert ids[0] == LENNOX_DOMAIN
        assert ids[1] == zone.unique_id


@pytest.mark.asyncio()
async def test_coast_subscription(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    zone = system.zone_list[0]
    sensor = S30CoastBinarySensor(hass, manager, system, zone)
    await sensor.async_added_to_hass()

    zone.heatCoast = False
    zone.coolCoast = False

    with patch.object(sensor, "schedule_update_ha_state") as update_callback:
        update_set = {
            "coolCoast": True,
        }
        zone.attr_updater(update_set, "coolCoast")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert sensor.is_on is True
        assert sensor.available is True

    with patch.object(sensor, "schedule_update_ha_state") as update_callback:
        update_set = {
            "coolCoast": False,
        }
        zone.attr_updater(update_set, "coolCoast")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert sensor.is_on is False
        assert sensor.available is True

    zone.heatCoast = False
    zone.coolCoast = False
    conftest_base_entity_availability(manager, system, sensor)


@pytest.mark.asyncio()
async def test_coast_created_when_not_zoned(hass, manager: Manager):
    """Coast sensors are created for a non-zoned system, and not for a zoned one"""
    system: lennox_system = manager.api.system_list[0]
    entry = manager.config_entry
    hass.data["lennoxs30"] = {}
    hass.data["lennoxs30"][entry.unique_id] = {MANAGER: manager}
    manager.api.isLANConnection = False

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    sensor_list = async_add_entities.call_args[0][0]
    coast_sensors = [sensor for sensor in sensor_list if isinstance(sensor, S30CoastBinarySensor)]
    assert len(coast_sensors) == len(system.zone_list)
    for sensor in coast_sensors:
        assert sensor.is_on is False
        assert sensor.name.endswith("_coasting")

    system.zoningMode = LENNOX_ZONING_MODE_ZONED
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    sensor_list = async_add_entities.call_args[0][0]
    assert [sensor for sensor in sensor_list if isinstance(sensor, S30CoastBinarySensor)] == []
