# pylint: disable=too-many-lines
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

import logging
from unittest.mock import patch
import pytest

from homeassistant.const import PERCENTAGE
from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT, SensorDeviceClass

from lennoxs30api.s30api_async import (
    LENNOX_BAD_STATUS,
    lennox_system,
    lennox_zone,
)
from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import LENNOX_DOMAIN
from custom_components.lennoxs30.sensor import S30HumiditySensor

from tests.conftest import conftest_base_entity_availability


@pytest.mark.asyncio
async def test_humidity_sensor(hass, manager: Manager, caplog):
    manager.is_metric = False
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.getZone(0)
    s = S30HumiditySensor(hass, manager, system, zone)

    assert s.unique_id == (system.unique_id + "_" + str(zone.id) + "_H").replace("-", "")
    assert s.name == system.name + "_" + zone.name + "_humidity"
    assert s.available is True
    assert s.should_poll is False
    assert s.available is True
    assert s.update() is True
    assert len(s.extra_state_attributes) == 0

    assert s.state == zone.humidity
    assert s.unit_of_measurement == PERCENTAGE

    assert s.device_class == SensorDeviceClass.HUMIDITY
    assert s.state_class == STATE_CLASS_MEASUREMENT

    identifiers = s.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == zone.unique_id

    for badstatus in LENNOX_BAD_STATUS:
        caplog.clear()
        with caplog.at_level(logging.WARNING):
            zone.humidityStatus = badstatus
            assert s.native_value is None
            assert len(caplog.records) == 1
            assert s.available is False
            assert len(caplog.records) == 2
            msg = caplog.messages[0]
            assert s._myname in msg
            assert badstatus in msg
            msg = caplog.messages[1]
            assert badstatus in msg
            assert s._myname in msg


@pytest.mark.asyncio
async def test_humidity_sensor_subscription(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.getZone(0)
    s = S30HumiditySensor(hass, manager, system, zone)
    await s.async_added_to_hass()

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        manager.is_metric = False
        update_set = {"humidity": zone.humidity + 1}
        zone.attr_updater(update_set, "humidity")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert s.state == zone.humidity

    conftest_base_entity_availability(manager, system, s)

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        manager.is_metric = False
        update_set = {"humidityStatus": "error"}
        zone.attr_updater(update_set, "humidityStatus")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert s.state is None
        assert s.available is False
