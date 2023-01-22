# pylint: disable=too-many-lines
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

import logging
from unittest.mock import patch
import pytest

from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT
from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT, DEVICE_CLASS_TEMPERATURE

from lennoxs30api.s30api_async import (
    LENNOX_STATUS_GOOD,
    LENNOX_STATUS_NOT_AVAILABLE,
    LENNOX_BAD_STATUS,
    lennox_system,
)

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import LENNOX_DOMAIN
from custom_components.lennoxs30.sensor import S30OutdoorTempSensor

from tests.conftest import conftest_base_entity_availability


@pytest.mark.asyncio
async def test_outdoor_temperature_sensor(hass, manager: Manager, caplog):
    manager.is_metric = False
    system: lennox_system = manager.api.system_list[0]
    s = S30OutdoorTempSensor(hass, manager, system)

    assert system.outdoorTemperatureStatus == LENNOX_STATUS_GOOD
    assert s.unique_id == (system.unique_id + "_OT").replace("-", "")
    assert s.available is True
    assert s.should_poll is False
    assert s.update() is True
    assert s.name == system.name + "_outdoor_temperature"
    assert len(s.extra_state_attributes) == 0
    manager.is_metric = False
    assert s.native_value == system.outdoorTemperature
    assert s.native_unit_of_measurement == TEMP_FAHRENHEIT
    manager.is_metric = True
    assert s.native_value == system.outdoorTemperatureC
    assert s.native_unit_of_measurement == TEMP_CELSIUS

    assert s.device_class == DEVICE_CLASS_TEMPERATURE
    assert s.state_class == STATE_CLASS_MEASUREMENT

    identifiers = s.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id + "_ou"

    for badstatus in LENNOX_BAD_STATUS:
        caplog.clear()
        with caplog.at_level(logging.WARNING):
            system.outdoorTemperatureStatus = badstatus
            assert s.native_value is None
            assert s.available is False
            assert len(caplog.records) == 1
            msg = caplog.messages[0]
            assert badstatus in msg


@pytest.mark.asyncio
async def test_outdoor_temperature_sensor_subscription(hass, manager: Manager):
    manager.is_metric = False
    system: lennox_system = manager.api.system_list[0]
    s = S30OutdoorTempSensor(hass, manager, system)
    await s.async_added_to_hass()

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        update_set = {"outdoorTemperature": system.outdoorTemperature + 1}
        system.attr_updater(update_set, "outdoorTemperature")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        update_set = {"outdoorTemperatureC": system.outdoorTemperatureC + 1}
        system.attr_updater(update_set, "outdoorTemperatureC")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    conftest_base_entity_availability(manager, system, s)

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        update_set = {"outdoorTemperatureStatus": LENNOX_STATUS_NOT_AVAILABLE}
        system.attr_updater(update_set, "outdoorTemperatureStatus")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
