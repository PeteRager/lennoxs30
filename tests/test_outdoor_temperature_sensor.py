import logging
from lennoxs30api.s30api_async import (
    LENNOX_STATUS_NOT_EXIST,
    LENNOX_STATUS_GOOD,
    LENNOX_STATUS_NOT_AVAILABLE,
    lennox_system,
)
from custom_components.lennoxs30 import (
    Manager,
)
import pytest
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.sensor import (
    S30OutdoorTempSensor,
)

from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT, DEVICE_CLASS_TEMPERATURE


from unittest.mock import patch


@pytest.mark.asyncio
async def test_outdoor_temperature_sensor(hass, manager: Manager, caplog):
    manager._is_metric = False
    system: lennox_system = manager._api._systemList[0]
    s = S30OutdoorTempSensor(hass, manager, system)

    assert system.outdoorTemperatureStatus == LENNOX_STATUS_GOOD
    assert s.unique_id == (system.unique_id() + "_OT").replace("-", "")
    assert s.should_poll == False
    assert s.name == system.name + "_outdoor_temperature"
    manager._is_metric = False
    assert s.state == system.outdoorTemperature
    assert s.unit_of_measurement == TEMP_FAHRENHEIT
    manager._is_metric = True
    assert s.state == system.outdoorTemperatureC
    assert s.unit_of_measurement == TEMP_CELSIUS

    assert s.device_class == DEVICE_CLASS_TEMPERATURE

    identifiers = s.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id() + "_ou"

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        system.outdoorTemperatureStatus = LENNOX_STATUS_NOT_EXIST
        assert s.state == None
        assert len(caplog.records) == 1
        msg = caplog.messages[0]
        assert LENNOX_STATUS_NOT_EXIST in msg

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        system.outdoorTemperatureStatus = LENNOX_STATUS_NOT_AVAILABLE
        assert s.state == None
        assert len(caplog.records) == 1
        msg = caplog.messages[0]
        assert LENNOX_STATUS_NOT_AVAILABLE in msg


@pytest.mark.asyncio
async def test_outdoor_temperature_sensor_subscription(hass, manager: Manager, caplog):
    manager._is_metric = False
    system: lennox_system = manager._api._systemList[0]
    s = S30OutdoorTempSensor(hass, manager, system)

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        set = {"outdoorTemperature": system.outdoorTemperature + 1}
        system.attr_updater(set, "outdoorTemperature")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        set = {"outdoorTemperatureC": system.outdoorTemperatureC + 1}
        system.attr_updater(set, "outdoorTemperatureC")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        set = {"outdoorTemperatureStatus": LENNOX_STATUS_NOT_AVAILABLE}
        system.attr_updater(set, "outdoorTemperatureStatus")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
