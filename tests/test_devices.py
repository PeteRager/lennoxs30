"""Test config flow."""

from ipaddress import IPv4Address
import logging
from unittest.mock import ANY, patch
from _pytest import config
from homeassistant.const import (
    CONF_EMAIL,
    CONF_HOST,
    CONF_HOSTS,
    CONF_PASSWORD,
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
)
from lennoxs30api.s30api_async import lennox_zone

import pytest
import os
import json

from homeassistant import config_entries, data_entry_flow
from custom_components.lennoxs30.config_flow import lennoxs30ConfigFlow
from custom_components.lennoxs30.const import (
    CONF_ALLERGEN_DEFENDER_SWITCH,
    CONF_CLOUD_CONNECTION,
    CONF_CREATE_INVERTER_POWER,
    CONF_CREATE_SENSORS,
    CONF_FAST_POLL_INTERVAL,
    CONF_MESSAGE_DEBUG_FILE,
    CONF_MESSAGE_DEBUG_LOGGING,
    CONF_PII_IN_MESSAGE_LOGS,
    CONF_APP_ID,
    LENNOX_DEFAULT_CLOUD_APP_ID,
    LENNOX_DEFAULT_LOCAL_APP_ID,
    LENNOX_MFG,
)


# from tests.common import MockConfigEntry

from custom_components.lennoxs30 import (
    DEFAULT_LOCAL_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    Manager,
    async_setup,
    create_migration_task,
)
from homeassistant.components import sensor
from homeassistant.helpers import entity_registry, entity_component

from custom_components.lennoxs30.util import redact_email

from homeassistant.helpers import device_registry as dr


def loadfile(name) -> json:
    script_dir = os.path.dirname(__file__) + "/messages/"
    file_path = os.path.join(script_dir, name)
    with open(file_path) as f:
        data = json.load(f)
    return data


@pytest.fixture
def manager(hass) -> Manager:

    config = config_entries.ConfigEntry(
        version=1, domain=DOMAIN, title="10.0.0.1", data={}, source="User"
    )
    config.unique_id = "12345"

    manager = Manager(
        hass=hass,
        config=config,
        email=None,
        password=None,
        poll_interval=1,
        fast_poll_interval=2,
        allergenDefenderSwitch=False,
        app_id="HA",
        conf_init_wait_time=30,
        ip_address="10.0.0.1",
        create_sensors=False,
        create_inverter_power=False,
        protocol="https",
        index=0,
        pii_message_logs=False,
        message_debug_logging=True,
        message_logging_file=None,
    )
    api = manager._api
    data = loadfile("login_response.json")
    api.process_login_response(data)

    data = loadfile("config_response_system_02.json")
    api.processMessage(data)

    data = loadfile("equipments_lcc_singlesetpoint.json")
    data["SenderID"] = "0000000-0000-0000-0000-000000000002"
    api.processMessage(data)

    data = loadfile("device_response_lcc.json")
    data["SenderID"] = "0000000-0000-0000-0000-000000000002"
    api.processMessage(data)

    return manager


@pytest.mark.asyncio
async def test_create_devices(hass, manager: Manager, caplog):
    device_registry = dr.async_get(hass)
    with patch.object(device_registry, "async_get_or_create") as mock_create_device:
        await manager.create_devices()
        call = mock_create_device.mock_calls[0]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["suggested_area"] == "basement"
        assert call.kwargs["name"] == manager._api._systemList[0].name
        assert call.kwargs["model"] == manager._api._systemList[0].productType
        assert call.kwargs["sw_version"] == manager._api._systemList[0].softwareVersion
        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == manager._api._systemList[0].unique_id()

        call = mock_create_device.mock_calls[1]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["suggested_area"] == "outside"
        assert call.kwargs["name"] == manager._api._systemList[0].name + " outdoor unit"
        assert call.kwargs["model"] == manager._api._systemList[0].outdoorUnitType
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager._api._systemList[0].unique_id()

        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == manager._api._systemList[0].unique_id() + "_ou"

        call = mock_create_device.mock_calls[2]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["suggested_area"] == "basement"
        assert call.kwargs["name"] == manager._api._systemList[0].name + " indoor unit"
        assert call.kwargs["model"] == manager._api._systemList[0].indoorUnitType
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager._api._systemList[0].unique_id()

        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == manager._api._systemList[0].unique_id() + "_iu"

        call = mock_create_device.mock_calls[3]
        zone: lennox_zone = manager._api._systemList[0]._zoneList[0]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["name"] == manager._api._systemList[0].name + "_" + zone.name
        assert call.kwargs["model"] == "thermostat"
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager._api._systemList[0].unique_id()

        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == zone.unique_id
