"""Diagnostics support for LennoxS30."""

# pylint: disable=line-too-long
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from . import MANAGER, Manager
from .const import LENNOX_DOMAIN


async def async_get_config_entry_diagnostics(hass: HomeAssistant, config_entry: ConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    manager: Manager = hass.data[LENNOX_DOMAIN][config_entry.unique_id][MANAGER]
    data: dict[str, Any] = {}

    data["config"] = {}
    for key, val in config_entry.data.items():
        data["config"][key] = val
    if CONF_PASSWORD in data["config"]:
        data["config"][CONF_PASSWORD] = "**redacted**"
    if CONF_EMAIL in data["config"]:
        data["config"][CONF_EMAIL] = "**redacted**"
    data["system"] = {}
    for system in manager.api.system_list:
        system_data: dict[str, any] = {
            "relayServer": system.relayServerConnected,
            "internet": system.internetStatus,
            "diagLevel": system.diagLevel,
            "cloud_status": system.cloud_status,
            "productType": system.productType,
            "sibling_identifier": system.sibling_identifier,
            "sibling_ip": system.sibling_ipAddress,
            "softwareVersion": system.softwareVersion,
            "sysUpTime": system.sysUpTime,
        }

        system_data["equipment"] = {}
        for eq_id, equipment in system.equipment.items():
            element = {
                "name": equipment.equipment_name,
                "eqType": equipment.equipType,
                "eqTypeName": equipment.equipment_type_name,
                "model": equipment.unit_model_number,
            }
            system_data["equipment"][eq_id] = element
        data["system"][system.sysId] = system_data

    data["comm_metrics"] = manager.getMetricsList()
    return data
