import logging
from lennoxs30api.s30api_async import (
    LENNOX_STATUS_NOT_EXIST,
    LENNOX_STATUS_GOOD,
    LENNOX_STATUS_NOT_AVAILABLE,
    lennox_system,
)
from custom_components.lennoxs30 import (
    DS_CONNECTED,
    DS_RETRY_WAIT,
    Manager,
)
import pytest
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.sensor import (
    S30OutdoorTempSensor,
)

from homeassistant.components.sensor import (
    STATE_CLASS_MEASUREMENT,
)


from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT, DEVICE_CLASS_TEMPERATURE


from unittest.mock import patch


@pytest.mark.asyncio
async def test_outdoor_temperature_sensor(hass, manager: Manager, caplog):
    manager.is_metric = False
    system: lennox_system = manager.api.system_list[0]
    s = S30OutdoorTempSensor(hass, manager, system)

    assert system.outdoorTemperatureStatus == LENNOX_STATUS_GOOD
    assert s.unique_id == (system.unique_id + "_OT").replace("-", "")
    assert s.available == True
    assert s.should_poll == False
    assert s.update() == True
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

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        system.outdoorTemperatureStatus = LENNOX_STATUS_NOT_EXIST
        assert s.native_value == None
        assert len(caplog.records) == 1
        msg = caplog.messages[0]
        assert LENNOX_STATUS_NOT_EXIST in msg

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        system.outdoorTemperatureStatus = LENNOX_STATUS_NOT_AVAILABLE
        assert s.native_value == None
        assert len(caplog.records) == 1
        msg = caplog.messages[0]
        assert LENNOX_STATUS_NOT_AVAILABLE in msg


@pytest.mark.asyncio
async def test_outdoor_temperature_sensor_subscription(hass, manager: Manager, caplog):
    manager.is_metric = False
    system: lennox_system = manager.api.system_list[0]
    s = S30OutdoorTempSensor(hass, manager, system)
    await s.async_added_to_hass()

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

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_RETRY_WAIT)
        assert update_callback.call_count == 1
        assert s.available == False

    c = s
    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_CONNECTED)
        assert update_callback.call_count == 1
        assert c.available == True
        system.attr_updater({"status": "online"}, "status", "cloud_status")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 2
        assert c.available == True
        system.attr_updater({"status": "offline"}, "status", "cloud_status")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 3
        assert c.available == False
