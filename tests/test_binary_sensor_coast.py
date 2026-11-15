"""Test the coasting binary sensor"""
# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring

from unittest.mock import Mock, patch

import pytest
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM
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
    assert sensor.extra_state_attributes == {"heatCoast": None, "coolCoast": None}

    # A partial update carries one flag and leaves the other unknown. The sensor
    # stays unavailable, because the unknown flag could be the active coast.
    zone.heatCoast = False
    zone.coolCoast = None
    assert sensor.available is False
    assert sensor.extra_state_attributes == {"heatCoast": False, "coolCoast": None}
    zone.heatCoast = None
    zone.coolCoast = False
    assert sensor.available is False

    # A known True already proves the sensor is on, whatever the other flag says.
    zone.heatCoast = True
    zone.coolCoast = None
    assert sensor.available is True
    assert sensor.state == "on"
    assert sensor.is_on is True
    assert sensor.extra_state_attributes == {"heatCoast": True, "coolCoast": None}
    zone.heatCoast = None
    zone.coolCoast = True
    assert sensor.available is True
    assert sensor.is_on is True
    assert sensor.extra_state_attributes == {"heatCoast": None, "coolCoast": True}

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
    assert sensor.extra_state_attributes == {"heatCoast": True, "coolCoast": False}
    zone.heatCoast = False
    zone.coolCoast = True
    assert sensor.state == "on"
    assert sensor.is_on is True
    assert sensor.extra_state_attributes == {"heatCoast": False, "coolCoast": True}

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
        assert sensor.extra_state_attributes == {"heatCoast": False, "coolCoast": True}

    with patch.object(sensor, "schedule_update_ha_state") as update_callback:
        update_set = {
            "coolCoast": False,
        }
        zone.attr_updater(update_set, "coolCoast")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert sensor.is_on is False
        assert sensor.available is True
        assert sensor.extra_state_attributes == {"heatCoast": False, "coolCoast": False}

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

    # Only active zones get a sensor - the inactive slots in the fixture are the
    # placeholders device setup skips, and they must not become permanent
    # unavailable entities.
    active_zones = [zone for zone in system.zone_list if zone.is_zone_active()]
    inactive_zones = [zone for zone in system.zone_list if not zone.is_zone_active()]
    assert inactive_zones, "the fixture must carry an inactive zone slot for this test to mean anything"
    assert len(coast_sensors) == len(active_zones)
    coast_unique_ids = {sensor.unique_id for sensor in coast_sensors}
    for zone in active_zones:
        assert (system.unique_id + "_" + str(zone.id)).replace("-", "") + UNIQUE_ID_SUFFIX_COAST_SENSOR in coast_unique_ids
    for zone in inactive_zones:
        assert (system.unique_id + "_" + str(zone.id)).replace("-", "") + UNIQUE_ID_SUFFIX_COAST_SENSOR not in coast_unique_ids

    for sensor in coast_sensors:
        assert sensor.is_on is False
        assert sensor.name.endswith("_coasting")

    system.zoningMode = LENNOX_ZONING_MODE_ZONED
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    sensor_list = async_add_entities.call_args[0][0]
    assert [sensor for sensor in sensor_list if isinstance(sensor, S30CoastBinarySensor)] == []


@pytest.mark.asyncio()
async def test_coast_skips_unnamed_inactive_zones(hass, manager: Manager):
    """An unnamed inactive slot cannot abort binary sensor setup"""
    system: lennox_system = manager.api.system_list[0]
    entry = manager.config_entry
    hass.data["lennoxs30"] = {}
    hass.data["lennoxs30"][entry.unique_id] = {MANAGER: manager}
    manager.api.isLANConnection = False
    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL

    for zone in system.zone_list:
        if not zone.is_zone_active():
            # The sensor name is built from the zone name, so an unnamed slot
            # would raise inside the constructor and take the setup with it.
            zone.name = None

    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    coast_sensors = [sensor for sensor in sensor_list if isinstance(sensor, S30CoastBinarySensor)]
    assert len(coast_sensors) == len([zone for zone in system.zone_list if zone.is_zone_active()])
    for sensor in coast_sensors:
        assert sensor.name.endswith("_coasting")


@pytest.mark.asyncio()
async def test_coast_on_us_customary_units(hass, manager_us_customary_units: Manager):
    """On a US customary units system the panel reports Fahrenheit and the sensor tracks it"""
    assert hass.config.units is US_CUSTOMARY_SYSTEM
    assert manager_us_customary_units.is_metric is False

    system: lennox_system = manager_us_customary_units.api.system_list[0]
    zone = system.zone_list[0]
    assert zone.is_zone_active() is True

    sensor = S30CoastBinarySensor(hass, manager_us_customary_units, system, zone)
    assert sensor.name == system.name + "_" + zone.name + "_coasting"
    assert sensor.available is True

    # The figure the panel sent on a US units system is the Fahrenheit one.
    assert zone.temperature == 79
    assert sensor.extra_state_attributes == {"heatCoast": False, "coolCoast": False}

    zone.heatCoast = True
    assert sensor.is_on is True
    assert sensor.state == "on"
    assert sensor.extra_state_attributes == {"heatCoast": True, "coolCoast": False}

    # Setup creates the coast sensor for the active zone on a US units system too.
    entry = manager_us_customary_units.config_entry
    hass.data["lennoxs30"] = {entry.unique_id: {MANAGER: manager_us_customary_units}}
    manager_us_customary_units.api.isLANConnection = False
    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    sensor_list = async_add_entities.call_args[0][0]
    coast_sensors = [sensor for sensor in sensor_list if isinstance(sensor, S30CoastBinarySensor)]
    assert len(coast_sensors) == len([zone for zone in system.zone_list if zone.is_zone_active()])
    assert len(coast_sensors) >= 1
