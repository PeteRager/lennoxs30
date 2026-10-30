# pylint: disable=too-many-lines
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

from unittest.mock import patch

import pytest
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import PERCENTAGE
from lennoxs30api.s30api_async import (
    lennox_system,
    lennox_zone,
)

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import LENNOX_DOMAIN
from custom_components.lennoxs30.sensor import S30ZoneDemandSensor
from tests.conftest import conftest_base_entity_availability


@pytest.mark.asyncio()
async def test_demand_sensor(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.getZone(0)
    s = S30ZoneDemandSensor(hass, manager, system, zone)

    assert s.unique_id == (system.unique_id + "_" + str(zone.id) + "_D").replace("-", "")
    assert s.name == system.name + "_" + zone.name + "_demand"
    assert s.available is True
    assert s.should_poll is False
    assert s.update() is True
    assert len(s.extra_state_attributes) == 0

    assert s.state == zone.demand
    assert s.unit_of_measurement == PERCENTAGE

    # Demand has no dedicated device class - it is a generic percentage measurement
    assert s.device_class is None
    assert s.state_class == SensorStateClass.MEASUREMENT

    identifiers = s.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == zone.unique_id


@pytest.mark.asyncio()
async def test_demand_sensor_subscription(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.getZone(0)
    s = S30ZoneDemandSensor(hass, manager, system, zone)
    await s.async_added_to_hass()

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        update_set = {"demand": (zone.demand or 0) + 10}
        zone.attr_updater(update_set, "demand")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert s.state == zone.demand

    conftest_base_entity_availability(manager, system, s)
