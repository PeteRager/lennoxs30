"""Test config flow."""

from unittest.mock import ANY, patch
from lennoxs30api.s30api_async import lennox_zone, LENNOX_NONE_STR

import pytest
import os
import json

from custom_components.lennoxs30.const import (
    LENNOX_MFG,
)


# from tests.common import MockConfigEntry

from custom_components.lennoxs30 import (
    DOMAIN,
    Manager,
)

from homeassistant.helpers import device_registry as dr


def loadfile(name) -> json:
    script_dir = os.path.dirname(__file__) + "/messages/"
    file_path = os.path.join(script_dir, name)
    with open(file_path) as f:
        data = json.load(f)
    return data


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


@pytest.mark.asyncio
async def test_create_devices_no_outdoor(hass, manager: Manager, caplog):
    device_registry = dr.async_get(hass)
    with patch.object(device_registry, "async_get_or_create") as mock_create_device:
        manager._api._systemList[0].outdoorUnitType = LENNOX_NONE_STR
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

        call = mock_create_device.mock_calls[2]
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


@pytest.mark.asyncio
async def test_create_devices_no_indoor(hass, manager: Manager, caplog):
    device_registry = dr.async_get(hass)
    with patch.object(device_registry, "async_get_or_create") as mock_create_device:
        manager._api._systemList[0].indoorUnitType = LENNOX_NONE_STR
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
