# pylint: disable=too-many-lines
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

import logging
from unittest.mock import patch
import pytest

from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT, SensorDeviceClass
from homeassistant.const import UnitOfTemperature,SIGNAL_STRENGTH_DECIBELS_MILLIWATT

from lennoxs30api.s30api_async import lennox_system

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import LENNOX_DOMAIN
from custom_components.lennoxs30.sensor_wifi import WifiRSSISensor

from tests.conftest import conftest_base_entity_availability, loadfile


@pytest.mark.asyncio
async def test_wifi_rssi_sensor(hass, manager: Manager, caplog):
    manager.is_metric = False
    system: lennox_system = manager.api.system_list[0]
    message = loadfile("wifi_interface_status.json", system.sysId)
    system.processMessage(message)

    s = WifiRSSISensor(hass, manager, system)

    assert s.unique_id == (system.unique_id + "_WIFI_RSSI").replace("-", "")
    assert s.available is True
    assert s.should_poll is False
    assert s.update() is True
    assert s.name == system.name + "_wifi_rssi"
    assert len(s.extra_state_attributes) == 8
    attrs = s.extra_state_attributes
    assert attrs["macAddr"] == "60:a4:4c:6b:d2:4c"
    assert attrs["ssid"] == "wifi_home"
    assert attrs["ip"] == "10.0.0.10"
    assert attrs["router"] == "10.0.0.1"
    assert attrs["dns"] == "8.8.8.8"
    assert attrs["dns2"] == "4.4.4.4"
    assert attrs["subnetMask"] == "255.255.0.0"
    assert attrs["bitRate"] == 72200000
    assert s.native_value == -68
    assert s.native_unit_of_measurement == SIGNAL_STRENGTH_DECIBELS_MILLIWATT

    assert s.device_class == SensorDeviceClass.SIGNAL_STRENGTH
    assert s.state_class == STATE_CLASS_MEASUREMENT

    identifiers = s.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id



@pytest.mark.asyncio
async def test_wifi_rssi_sensor_subscription(hass, manager: Manager):
    manager.is_metric = False
    system: lennox_system = manager.api.system_list[0]
    message = loadfile("wifi_interface_status.json", system.sysId)
    system.processMessage(message)
    s = WifiRSSISensor(hass, manager, system)
    await s.async_added_to_hass()

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        update_set = {"wifi_rssi": system.wifi_rssi + 1}
        system.attr_updater(update_set, "wifi_rssi")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert s.native_value == -67

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        update_set = {"wifi_macAddr": "newMac"}
        system.attr_updater(update_set, "wifi_macAddr")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert s.extra_state_attributes["macAddr"] == "newMac"

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        update_set = {"wifi_ssid": "newSSID"}
        system.attr_updater(update_set, "wifi_ssid")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert s.extra_state_attributes["ssid"] == "newSSID"

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        update_set = {"wifi_ip": "1.1.1.1"}
        system.attr_updater(update_set, "wifi_ip")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert s.extra_state_attributes["ip"] == "1.1.1.1"

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        update_set = {"wifi_router": "2.2.2.2"}
        system.attr_updater(update_set, "wifi_router")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert s.extra_state_attributes["router"] == "2.2.2.2"

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        update_set = {"wifi_dns": "3.3.3.3"}
        system.attr_updater(update_set, "wifi_dns")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert s.extra_state_attributes["dns"] == "3.3.3.3"

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        update_set = {"wifi_dns2": "5.5.5.5"}
        system.attr_updater(update_set, "wifi_dns2")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert s.extra_state_attributes["dns2"] == "5.5.5.5"

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        update_set = {"wifi_subnetMask": "255.255.255.0"}
        system.attr_updater(update_set, "wifi_subnetMask")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert s.extra_state_attributes["subnetMask"] == "255.255.255.0"

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        update_set = {"wifi_bitRate": 10 }
        system.attr_updater(update_set, "wifi_bitRate")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert s.extra_state_attributes["bitRate"] == 10

    conftest_base_entity_availability(manager, system, s)