"""Test the diagnostics"""
# pylint: disable=line-too-long
import pytest

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import MANAGER
from custom_components.lennoxs30.diagnostics import async_get_config_entry_diagnostics
from homeassistant import config_entries


@pytest.mark.asyncio
async def test_diagnostics_local(
    hass, manager_system_04_furn_ac_zoning_ble: Manager, config_entry_local: config_entries.ConfigEntry
):
    """Test the alert sensor"""
    manager = manager_system_04_furn_ac_zoning_ble
    entry = manager.config_entry = config_entry_local
    hass.data["lennoxs30"] = {}
    hass.data["lennoxs30"][entry.unique_id] = {MANAGER: manager}
    diags = await async_get_config_entry_diagnostics(hass, entry)

    assert "config" in diags
    assert diags["config"]["host"] == "10.0.0.1"
    assert "system" in diags
    assert "0000000-0000-0000-0000-000000000001" in diags["system"]
    system = diags["system"]["0000000-0000-0000-0000-000000000001"]
    assert len(system["equipment"]) == 4
    assert "comm_metrics" in diags
    assert diags["comm_metrics"]["message_count"] == 6


@pytest.mark.asyncio
async def test_diagnostics_cloud(
    hass, manager_system_04_furn_ac_zoning_ble: Manager, config_entry_cloud: config_entries.ConfigEntry
):
    """Test the alert sensor"""
    manager = manager_system_04_furn_ac_zoning_ble
    entry = manager.config_entry = config_entry_cloud
    hass.data["lennoxs30"] = {}
    hass.data["lennoxs30"][entry.unique_id] = {MANAGER: manager}
    diags = await async_get_config_entry_diagnostics(hass, entry)

    assert "config" in diags
    assert diags["config"]["password"] == "**redacted**"
    assert diags["config"]["email"] == "**redacted**"
    assert "system" in diags
    assert "0000000-0000-0000-0000-000000000001" in diags["system"]
    system = diags["system"]["0000000-0000-0000-0000-000000000001"]
    assert len(system["equipment"]) == 4
    assert "comm_metrics" in diags
    assert diags["comm_metrics"]["message_count"] == 6
