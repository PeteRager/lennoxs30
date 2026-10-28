"""Tests for Lennox mDNS discovery and migration."""

import json
from ipaddress import IPv4Address
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import SOURCE_ZEROCONF
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.lennoxs30 import async_setup
from custom_components.lennoxs30.config_flow import Lennoxs30ConfigFlow, async_migrate_zeroconf_entry
from custom_components.lennoxs30.discovery import (
    LennoxServiceListener,
    HTTP_SERVICE,
    ZEROCONF_SERVICE,
    advertised_identity,
    discovered_host,
    discovered_port,
    is_lennox_service,
    runtime_target,
)


def test_manifest_declares_zeroconf_dependency():
    with open("custom_components/lennoxs30/manifest.json", encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)

    assert "zeroconf" in manifest["dependencies"]
    assert ZEROCONF_SERVICE in manifest["zeroconf"]
    # Some Lennox thermostats incorrectly arrive as _http services with the
    # Lennox service type embedded in the instance name.
    assert {
        "name": "*_icomfort4._res._lii._http._tcp.local.*",
        "type": HTTP_SERVICE,
    } in manifest["zeroconf"]


def service_info(**kwargs):
    values = {
        "type": ZEROCONF_SERVICE,
        "hostname": "Lennox-S40-BT23M54549.local.",
        "name": "Lennox-S40-BT23M54549._icomfort4._res._lii._http._tcp.local.",
        "host": "192.168.1.40",
        "ip_address": IPv4Address("192.168.1.40"),
        "ip_addresses": [IPv4Address("192.168.1.40")],
        "port": 443,
        "properties": {"serialNumber": "BT23M54549"},
    }
    values.update(kwargs)
    return SimpleNamespace(**values)


def test_discovery_preserves_hostname_port_and_identity():
    info = service_info()
    assert discovered_host(info) == "lennox-s40-bt23m54549.local"
    assert discovered_port(info) == 443
    assert runtime_target(info) == "192.168.1.40:443"
    assert advertised_identity(info) == "BT23M54549"


def test_discovery_defaults_port_and_handles_missing_txt():
    info = service_info(port=None, properties={})
    assert discovered_port(info) == 443
    assert advertised_identity(info) is None


def test_discovery_extracts_identity_from_service_instance_name():
    info = service_info(properties={}, name="_BT23M54601_1._icomfort4._res._lii._http._tcp.local.")
    assert advertised_identity(info) == "BT23M54601"


def test_malformed_http_service_matches_only_lennox_instance():
    malformed_name = "_BT23M54601_1._icomfort4._res._lii._http._tcp.local._http._tcp.local."
    assert is_lennox_service(HTTP_SERVICE, malformed_name)
    assert not is_lennox_service(HTTP_SERVICE, "printer._http._tcp.local.")


@pytest.mark.asyncio
async def test_async_setup_awaits_shared_zeroconf_instance(hass, mock_async_zeroconf):
    aiozc = mock_async_zeroconf
    aiozc.async_add_service_listener = AsyncMock()
    aiozc.async_remove_service_listener = AsyncMock()

    assert await async_setup(hass, {}) is True

    assert aiozc.async_add_service_listener.await_count == 2


@pytest.mark.asyncio
async def test_shared_zeroconf_listener_processes_service_update(hass, mock_async_zeroconf):
    aiozc = mock_async_zeroconf
    service = MagicMock()
    aiozc.async_get_service_info = AsyncMock(return_value=service)
    listener = LennoxServiceListener(hass, aiozc)

    with patch(
        "custom_components.lennoxs30.discovery.info_from_service",
        return_value=service_info(),
    ), patch(
        "custom_components.lennoxs30.config_flow.async_migrate_zeroconf_entry",
        new=AsyncMock(return_value=True),
    ) as migrate:
        await listener._process_service(ZEROCONF_SERVICE, service_info().name)

    aiozc.async_get_service_info.assert_awaited_once_with(ZEROCONF_SERVICE, service_info().name)
    migrate.assert_awaited_once_with(hass, service_info())


@pytest.mark.asyncio
async def test_zeroconf_existing_ip_entry_migrates_without_duplicate(hass):
    entry = MockConfigEntry(
        domain="lennoxs30",
        unique_id="existing-entry",
        data={"cloud_connection": False, "host": "192.168.1.40", "create_sensors": True},
    )
    entry.add_to_hass(hass)
    hass.data["lennoxs30"] = {}
    flow = Lennoxs30ConfigFlow()
    flow.hass = hass

    with patch.object(hass.config_entries, "async_update_entry") as update_entry:
        result = await flow.async_step_zeroconf(service_info())

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
    updated = update_entry.call_args.kwargs["data"]
    assert updated["host"] == "lennox-s40-bt23m54549.local"
    assert updated["mdns_port"] == 443
    assert updated["create_sensors"] is True
    assert update_entry.call_args.kwargs["title"] == "lennox-s40-bt23m54549.local"
    assert update_entry.call_args.kwargs["unique_id"] == "lennoxs30_BT23M54549"


@pytest.mark.asyncio
async def test_zeroconf_migration_updates_real_config_entry(hass):
    entry = MockConfigEntry(
        domain="lennoxs30",
        title="192.168.1.40",
        unique_id="lennoxs30_192.168.1.40",
        data={"cloud_connection": False, "host": "192.168.1.40", "keep": "me"},
    )
    entry.add_to_hass(hass)
    entry_id = entry.entry_id
    flow = Lennoxs30ConfigFlow()
    flow.hass = hass

    result = await flow.async_step_zeroconf(service_info())

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
    assert entry.entry_id == entry_id
    assert entry.title == "lennox-s40-bt23m54549.local"
    assert entry.unique_id == "lennoxs30_BT23M54549"
    assert entry.data["host"] == "lennox-s40-bt23m54549.local"
    assert entry.data["mdns_port"] == 443
    assert entry.data["keep"] == "me"


@pytest.mark.asyncio
async def test_zeroconf_does_not_match_cloud_entry(hass):
    entry = MockConfigEntry(
        domain="lennoxs30",
        unique_id="cloud-entry",
        data={"cloud_connection": True, "email": "user@example.com"},
    )
    entry.add_to_hass(hass)
    flow = Lennoxs30ConfigFlow()
    flow.hass = hass

    with patch.object(flow, "async_set_unique_id"), patch.object(flow, "_abort_if_unique_id_configured"):
        result = await flow.async_step_zeroconf(service_info(properties={"id": "thermostat-1"}))

    assert result["type"] == "form"
    assert result["step_id"] == "advanced"
    assert flow.config_input["host"] == "lennox-s40-bt23m54549.local"
    assert flow.config_input["thermostat_id"] == "thermostat-1"


@pytest.mark.asyncio
async def test_zeroconf_migration_ignores_cloud_entry(hass):
    entry = MockConfigEntry(
        domain="lennoxs30",
        unique_id="cloud-entry",
        data={"cloud_connection": True, "email": "user@example.com"},
    )
    entry.add_to_hass(hass)

    with patch.object(hass.config_entries, "async_update_entry") as update_entry:
        migrated = await async_migrate_zeroconf_entry(hass, service_info())

    assert migrated is False
    update_entry.assert_not_called()


@pytest.mark.asyncio
async def test_zeroconf_full_home_assistant_flow(hass, mock_zeroconf):
    mock_zeroconf.return_value.async_unregister_all_services = AsyncMock()
    mock_zeroconf.return_value._async_close = AsyncMock()
    with patch("custom_components.lennoxs30.async_setup_entry", new=AsyncMock(return_value=True)):
        result = await hass.config_entries.flow.async_init(
            "lennoxs30", context={"source": SOURCE_ZEROCONF}, data=service_info(properties={"id": "thermostat-1"})
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "advanced"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "scan_interval": 1,
                "fast_scan_interval": 0.75,
                "fast_scan_count": 10,
                "init_wait_time": 30,
                "timeout": 30,
                "pii_in_message_logs": False,
                "message_debug_logging": True,
                "log_messages_to_file": False,
                "message_debug_file": "",
            },
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["host"] == "lennox-s40-bt23m54549.local"
    assert result["data"]["mdns_port"] == 443


@pytest.mark.asyncio
async def test_malformed_http_zeroconf_flow_is_supported(hass, mock_zeroconf):
    mock_zeroconf.return_value.async_unregister_all_services = AsyncMock()
    mock_zeroconf.return_value._async_close = AsyncMock()
    malformed_info = service_info(
        type=HTTP_SERVICE,
        name="_BT23M54549_1._icomfort4._res._lii._http._tcp.local._http._tcp.local.",
        properties={"id": "thermostat-1"},
    )
    with patch("custom_components.lennoxs30.async_setup_entry", new=AsyncMock(return_value=True)):
        result = await hass.config_entries.flow.async_init("lennoxs30", context={"source": SOURCE_ZEROCONF}, data=malformed_info)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "advanced"


@pytest.mark.asyncio
async def test_malformed_http_existing_entry_migrates(hass):
    entry = MockConfigEntry(
        domain="lennoxs30",
        unique_id="existing-entry",
        data={
            "cloud_connection": False,
            "host": "192.168.1.40",
            "thermostat_id": "BT23M54549",
            "keep": "me",
        },
    )
    entry.add_to_hass(hass)
    malformed_info = service_info(
        type=HTTP_SERVICE,
        host="192.168.1.198",
        hostname="Lennox-S40-BT23M54549.local.",
        name="_BT23M54549_1._icomfort4._res._lii._http._tcp.local._http._tcp.local.",
        properties={},
    )
    flow = Lennoxs30ConfigFlow()
    flow.hass = hass

    with patch.object(hass.config_entries, "async_update_entry") as update_entry:
        result = await flow.async_step_zeroconf(malformed_info)

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
    updated = update_entry.call_args.kwargs["data"]
    assert updated["host"] == "lennox-s40-bt23m54549.local"
    assert updated["mdns_port"] == 443
    assert updated["keep"] == "me"
    assert update_entry.call_args.kwargs["title"] == "lennox-s40-bt23m54549.local"
    assert update_entry.call_args.kwargs["unique_id"] == "lennoxs30_BT23M54549"


@pytest.mark.asyncio
async def test_zeroconf_new_ip_uses_api_identity_to_migrate(hass):
    entry = MockConfigEntry(
        domain="lennoxs30",
        unique_id="existing-entry",
        data={"cloud_connection": False, "host": "192.168.1.40", "thermostat_id": "thermostat-1", "keep": "me"},
    )
    entry.add_to_hass(hass)
    flow = Lennoxs30ConfigFlow()
    flow.hass = hass

    with patch.object(flow, "_probe_discovered_identity", return_value="thermostat-1") as probe, patch.object(
        hass.config_entries, "async_update_entry"
    ) as update_entry:
        result = await flow.async_step_zeroconf(service_info(host="192.168.1.61", properties={}))

    assert result["reason"] == "already_configured"
    probe.assert_awaited_once()
    updated = update_entry.call_args.kwargs["data"]
    assert updated["host"] == "lennox-s40-bt23m54549.local"
    assert updated["thermostat_id"] == "thermostat-1"
    assert updated["keep"] == "me"


@pytest.mark.asyncio
async def test_zeroconf_probe_failure_keeps_discovery_available(hass):
    flow = Lennoxs30ConfigFlow()
    flow.hass = hass

    with patch.object(flow, "_probe_discovered_identity", return_value=None) as probe, patch.object(
        flow, "async_set_unique_id"
    ), patch.object(flow, "_abort_if_unique_id_configured"):
        result = await flow.async_step_zeroconf(service_info(properties={}))

    assert result["type"] == "form"
    assert result["step_id"] == "advanced"
    assert flow.config_input["host"] == "lennox-s40-bt23m54549.local"
    assert "thermostat_id" not in flow.config_input
    probe.assert_awaited_once()


@pytest.mark.asyncio
async def test_zeroconf_rediscovery_updates_loaded_manager(hass):
    entry = MockConfigEntry(
        domain="lennoxs30",
        unique_id="existing-entry",
        data={"cloud_connection": False, "host": "lennox-s40.local", "thermostat_id": "thermostat-1"},
    )
    entry.add_to_hass(hass)
    manager = MagicMock()
    hass.data["lennoxs30"] = {"existing-entry": {"manager": manager}}
    flow = Lennoxs30ConfigFlow()
    flow.hass = hass

    with patch.object(hass.config_entries, "async_update_entry") as update_entry:
        result = await flow.async_step_zeroconf(
            service_info(host="192.168.1.61", hostname="Lennox-S40.local.", properties={"id": "thermostat-1"})
        )

    assert result["reason"] == "already_configured"
    manager.async_update_connection_target.assert_called_once_with("lennox-s40.local", "192.168.1.61", 443)
    assert update_entry.call_args.kwargs["unique_id"] == "lennoxs30_thermostat-1"


@pytest.mark.asyncio
async def test_zeroconf_matches_existing_device_registry_identity(hass):
    entry = MockConfigEntry(
        domain="lennoxs30",
        unique_id="lennoxs30_192.168.1.250",
        data={"cloud_connection": False, "host": "192.168.1.250"},
    )
    entry.add_to_hass(hass)
    hass.data["lennoxs30"] = {}
    registry = SimpleNamespace(
        devices={
            "device": SimpleNamespace(
                config_entries={entry.entry_id},
                identifiers={("lennoxs30", "BT23M54601")},
            )
        }
    )
    assert (
        advertised_identity(
            service_info(
                name="_BT23M54601_1._icomfort4._res._lii._http._tcp.local.",
                properties={},
            )
        )
        == "BT23M54601"
    )
    flow = Lennoxs30ConfigFlow()
    flow.hass = hass

    with patch.object(hass.config_entries, "async_update_entry") as update_entry, patch(
        "custom_components.lennoxs30.config_flow.dr.async_get", return_value=registry
    ):
        result = await flow.async_step_zeroconf(
            service_info(
                host="192.168.1.198",
                hostname="Lennox-S40-BT23M54601.local.",
                name="_BT23M54601_1._icomfort4._res._lii._http._tcp.local.",
                properties={},
            )
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
    assert update_entry.call_args.kwargs["data"]["host"] == "lennox-s40-bt23m54601.local"


def test_manager_target_update_replaces_stale_runtime_ip(manager):
    manager.api.isLANConnection = True
    manager.async_update_connection_target("lennox-s40-bt23m54601.local", "192.168.1.61", 443)
    assert manager._ip_address == "lennox-s40-bt23m54601.local:443"
    assert manager._resolved_ip == "192.168.1.61"
    assert manager.api.ip == "192.168.1.61:443"
    assert manager._reinitialize is True


def test_manager_target_update_does_not_change_cloud_manager(manager):
    manager.api.isLANConnection = False
    manager.api.ip = None
    manager.async_update_connection_target("lennox-s40.local", "192.168.1.10", 443)
    assert manager.api.ip is None
