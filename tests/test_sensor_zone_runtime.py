"""Tests for zone runtime sensors."""

from unittest.mock import patch

import pytest
from homeassistant.const import PERCENTAGE

from lennoxs30api.s30api_async import lennox_system, lennox_zone
from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import (
    LENNOX_DOMAIN,
    UNIQUE_ID_SUFFIX_ZONE_AIR_DEMAND,
    UNIQUE_ID_SUFFIX_ZONE_HUMIDITY_OPERATION,
)
from custom_components.lennoxs30.sensor import S30ZoneAirDemandSensor, S30ZoneHumidityOperationSensor
from tests.conftest import conftest_base_entity_availability


@pytest.mark.asyncio
async def test_zone_runtime_sensors_init(hass, manager: Manager):
    """Test zone runtime sensors."""
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.getZone(0)

    humidity_operation = S30ZoneHumidityOperationSensor(hass, manager, system, zone)
    air_demand = S30ZoneAirDemandSensor(hass, manager, system, zone)

    assert humidity_operation.unique_id == (zone.unique_id + UNIQUE_ID_SUFFIX_ZONE_HUMIDITY_OPERATION).replace(
        "-", ""
    )
    assert air_demand.unique_id == (zone.unique_id + UNIQUE_ID_SUFFIX_ZONE_AIR_DEMAND).replace("-", "")

    assert humidity_operation.entity_category == "diagnostic"
    assert air_demand.entity_category == "diagnostic"
    assert air_demand.native_unit_of_measurement == PERCENTAGE

    zone.humOperation = "dehumidifying"
    zone.demand = 42.5
    assert humidity_operation.native_value == "dehumidifying"
    assert air_demand.native_value == 42.5

    zone.humOperation = None
    zone.demand = "not-a-number"
    assert humidity_operation.native_value is None
    assert air_demand.native_value is None

    identifiers = air_demand.device_info["identifiers"]
    for ids in identifiers:
        assert ids[0] == LENNOX_DOMAIN
        assert ids[1] == zone.unique_id


@pytest.mark.asyncio
async def test_zone_runtime_sensors_subscription(hass, manager: Manager):
    """Test zone runtime sensor subscriptions."""
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.getZone(0)

    humidity_operation = S30ZoneHumidityOperationSensor(hass, manager, system, zone)
    await humidity_operation.async_added_to_hass()
    with patch.object(humidity_operation, "schedule_update_ha_state") as update_callback:
        zone.attr_updater({"humOperation": "dehumidifying"}, "humOperation")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert humidity_operation.native_value == "dehumidifying"

    air_demand = S30ZoneAirDemandSensor(hass, manager, system, zone)
    await air_demand.async_added_to_hass()
    with patch.object(air_demand, "schedule_update_ha_state") as update_callback:
        zone.attr_updater({"demand": 18.5}, "demand")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert air_demand.native_value == 18.5

    conftest_base_entity_availability(manager, system, humidity_operation)
