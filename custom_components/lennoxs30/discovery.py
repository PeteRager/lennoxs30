"""Lennox mDNS discovery helpers."""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from homeassistant.components.zeroconf.discovery import info_from_service
from homeassistant.core import HomeAssistant
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from zeroconf import ServiceListener, Zeroconf
from zeroconf.asyncio import AsyncServiceInfo, AsyncZeroconf

from .const import CONF_THERMOSTAT_ID

ZEROCONF_SERVICE = "_icomfort4._res._lii._http._tcp.local."
# Some Lennox thermostats publish the Lennox service as an _http service and
# include the intended service type in the instance name instead.
HTTP_SERVICE = "_http._tcp.local."
LENNOX_SERVICE_MARKER = "_icomfort4._res._lii._http._tcp.local."
DEFAULT_PORT = 443
_ID_KEYS = ("id", "uuid", "device_id", "deviceId", "thermostat_id", "thermostatId", "sysId", "serial", "serialNumber")


def normalize_hostname(hostname: str) -> str:
    """Normalize a Zeroconf hostname for comparison and storage."""
    return hostname.rstrip(".").lower()


def is_lennox_service(type_: str, name: str) -> bool:
    """Return whether a Zeroconf record identifies a Lennox thermostat."""
    if type_ == ZEROCONF_SERVICE:
        return True
    return type_ == HTTP_SERVICE and LENNOX_SERVICE_MARKER in name.lower()


def discovered_host(info: ZeroconfServiceInfo) -> str:
    """Return the durable hostname from a discovery result."""
    return normalize_hostname(info.hostname or info.name.split(".", 1)[0])


def discovered_port(info: ZeroconfServiceInfo) -> int:
    """Return the advertised port, defaulting to Lennox's HTTPS port."""
    return info.port or DEFAULT_PORT


def runtime_target(info: ZeroconfServiceInfo) -> str:
    """Return the address used by the legacy API client for this result."""
    return f"{info.host}:{discovered_port(info)}"


def advertised_identity(info: ZeroconfServiceInfo) -> str | None:
    """Extract a stable thermostat identity from mDNS TXT properties."""
    properties: Mapping[str, Any] = info.properties
    for key in _ID_KEYS:
        value = properties.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()

    # Lennox includes the thermostat identifier in the service instance name,
    # e.g. ``_BT23M54601_1._icomfort4...``. The trailing numeric component is
    # an mDNS instance discriminator and is not part of the device identity.
    instance = info.name.split(".", 1)[0].strip("_")
    match = re.fullmatch(r"(BT[A-Z0-9]+?)(?:_\d+)?", instance, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def entry_identity(data: Mapping[str, Any]) -> str | None:
    """Return the stable identity stored for a discovered entry."""
    value = data.get(CONF_THERMOSTAT_ID)
    return str(value) if value else None


class LennoxServiceListener(ServiceListener):
    """Track Lennox services using Home Assistant's shared Zeroconf instance."""

    def __init__(self, hass: HomeAssistant, aiozc: AsyncZeroconf) -> None:
        """Initialize the listener."""
        self._hass = hass
        self._aiozc = aiozc

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle a service being added."""
        self._hass.async_create_task(self._process_service(type_, name))

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle a service being updated."""
        self._hass.async_create_task(self._process_service(type_, name))

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Ignore temporary service removal; the config entry is retained."""

    async def _process_service(self, type_: str, name: str) -> None:
        """Resolve and migrate a discovered service."""
        if not is_lennox_service(type_, name):
            return
        service = await self._aiozc.async_get_service_info(type_, name)
        if not service:
            return
        info = info_from_service(service)
        if not info:
            return
        from .config_flow import async_migrate_zeroconf_entry

        await async_migrate_zeroconf_entry(self._hass, info)
