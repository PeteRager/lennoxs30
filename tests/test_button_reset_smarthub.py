"""Tests the reset smart hub button"""
# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring

from unittest.mock import patch
import logging
import pytest

from lennoxs30api.s30api_async import lennox_system
from lennoxs30api.s30exception import S30Exception

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import LENNOX_DOMAIN
from custom_components.lennoxs30.button import ResetSmartHubButton

from tests.conftest import conftest_base_entity_availability


@pytest.mark.asyncio
async def test_button_reset_smarthub_unique_id(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    button = ResetSmartHubButton(hass, manager, system)
    assert button.unique_id == f"{system.unique_id}_RESET_SMART_HUB".replace("-", "")


@pytest.mark.asyncio
async def test_button_reset_smarthub_name(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    button = ResetSmartHubButton(hass, manager, system)
    assert button.name == "South Moetown_reset_smarthub"


@pytest.mark.asyncio
async def test_button_reset_smarthub_subscription(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    button = ResetSmartHubButton(hass, manager, system)
    await button.async_added_to_hass()
    conftest_base_entity_availability(manager, system, button)


@pytest.mark.asyncio
async def test_button_reset_smarthub_async_press(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    button = ResetSmartHubButton(hass, manager, system)

    with patch.object(system, "reset_smart_controller") as reset_smart_controller:
        await button.async_press()
        assert reset_smart_controller.call_count == 1

    with caplog.at_level(logging.ERROR):
        with patch.object(system, "reset_smart_controller") as reset_smart_controller:
            caplog.clear()
            reset_smart_controller.side_effect = S30Exception("This is the error", 100, 200)
            await button.async_press()
            assert len(caplog.records) == 1
            assert "ResetSmartHubButton::async_press" in caplog.messages[0]
            assert "This is the error" in caplog.messages[0]

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(system, "reset_smart_controller") as reset_smart_controller:
            reset_smart_controller.side_effect = ValueError("This is the error")
            await button.async_press()
            assert reset_smart_controller.call_count == 1
            assert len(caplog.records) == 1
            msg = caplog.messages[0]
            assert "This is the error" in msg
            assert "unexpected" in msg
            assert button.name in msg


@pytest.mark.asyncio
async def test_button_reset_smarthub_device_info(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    await manager.create_devices()
    button = ResetSmartHubButton(hass, manager, system)

    identifiers = button.device_info["identifiers"]
    for ids in identifiers:
        assert ids[0] == LENNOX_DOMAIN
        assert ids[1] == system.unique_id


def test_button_reset_smarthub_entity_category(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    button = ResetSmartHubButton(hass, manager, system)
    assert button.entity_category == "diagnostic"
