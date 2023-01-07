# pylint: disable=too-many-lines
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

import logging
from unittest.mock import patch
import pytest

from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT, DEVICE_CLASS_TEMPERATURE
from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT

from lennoxs30api.s30api_async import (
    LENNOX_BAD_STATUS,
    lennox_system,
    lennox_zone,
)
from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import LENNOX_DOMAIN
from custom_components.lennoxs30.sensor import S30TempSensor

from tests.conftest import conftest_base_entity_availability


@pytest.mark.asyncio
async def test_temperature_sensor(hass, manager: Manager, caplog):
    manager.is_metric = False
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.getZone(0)
    s = S30TempSensor(hass, manager, system, zone)

    assert s.unique_id == (system.unique_id + "_" + str(zone.id) + "_T").replace("-", "")
    assert s.name == system.name + "_" + zone.name + "_temperature"
    assert s.available is True
    assert s.should_poll is False
    assert s.available is True
    assert s.update() is True
    assert len(s.extra_state_attributes) == 0

    manager.is_metric = False
    assert s.native_value == zone.temperature
    assert s.native_unit_of_measurement == TEMP_FAHRENHEIT
    manager.is_metric = True
    assert s.native_value == zone.temperatureC
    assert s.native_unit_of_measurement == TEMP_CELSIUS

    assert s.device_class == DEVICE_CLASS_TEMPERATURE
    assert s.state_class == STATE_CLASS_MEASUREMENT

    identifiers = s.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == zone.unique_id

    for badstatus in LENNOX_BAD_STATUS:
        caplog.clear()
        with caplog.at_level(logging.WARNING):
            zone.temperatureStatus = badstatus
            assert s.native_value is None
            assert s.available is False
            assert len(caplog.records) == 1
            msg = caplog.messages[0]
            assert badstatus in msg


@pytest.mark.asyncio
async def test_temperature_sensor_subscription(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.getZone(0)
    s = S30TempSensor(hass, manager, system, zone)
    await s.async_added_to_hass()

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        manager.is_metric = False
        update_set = {"temperature": zone.temperature + 1}
        zone.attr_updater(update_set, "temperature")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert s.native_value == zone.temperature

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        manager.is_metric = True
        update_set = {"temperatureC": zone.temperatureC + 1}
        zone.attr_updater(update_set, "temperatureC")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert s.native_value == zone.temperatureC

    conftest_base_entity_availability(manager, system, s)
