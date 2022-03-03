"""Test config flow."""

from ipaddress import IPv4Address
import logging
from unittest.mock import ANY, patch
from homeassistant.const import (
    CONF_EMAIL,
    CONF_HOST,
    CONF_HOSTS,
    CONF_PASSWORD,
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
)

import pytest

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
    DEFAULT_CLOUD_TIMEOUT,
    LENNOX_DEFAULT_CLOUD_APP_ID,
    LENNOX_DEFAULT_LOCAL_APP_ID,
)


# from tests.common import MockConfigEntry

from custom_components.lennoxs30 import (
    DEFAULT_LOCAL_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    async_migrate_entry,
    async_setup,
    create_migration_task,
)
from homeassistant.components import sensor
from homeassistant.helpers import entity_registry, entity_component

from custom_components.lennoxs30.util import redact_email

# User Flows


@pytest.mark.asyncio
async def test_migrate_local_config_min(hass, caplog):
    config = {
        DOMAIN: {
            CONF_EMAIL: "myemail@email.com",
            CONF_PASSWORD: "mypassword",
            CONF_HOSTS: "10.0.0.1",
            CONF_FAST_POLL_INTERVAL: 0.75,
            CONF_ALLERGEN_DEFENDER_SWITCH: False,
            CONF_CREATE_SENSORS: False,
            CONF_CREATE_INVERTER_POWER: False,
            CONF_PROTOCOL: "https",
            CONF_PII_IN_MESSAGE_LOGS: False,
            CONF_MESSAGE_DEBUG_FILE: "",
            CONF_MESSAGE_DEBUG_LOGGING: True,
        }
    }
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        with patch(
            "custom_components.lennoxs30.create_migration_task"
        ) as mock_migration_task:
            await async_setup(hass, config)
            assert mock_migration_task.call_count == 1
            migration_data = mock_migration_task.call_args[0][1]
            assert migration_data[CONF_SCAN_INTERVAL] == DEFAULT_LOCAL_POLL_INTERVAL
            assert CONF_EMAIL not in migration_data
            assert CONF_PASSWORD not in migration_data
            assert CONF_HOSTS not in migration_data
            assert migration_data[CONF_HOST] == "10.0.0.1"
            assert migration_data[CONF_FAST_POLL_INTERVAL] == 0.75
            assert migration_data[CONF_CREATE_SENSORS] == False
            assert migration_data[CONF_ALLERGEN_DEFENDER_SWITCH] == False
            assert migration_data[CONF_CREATE_INVERTER_POWER] == False
            assert migration_data[CONF_PROTOCOL] == "https"
            assert migration_data[CONF_PII_IN_MESSAGE_LOGS] == False
            assert migration_data[CONF_MESSAGE_DEBUG_FILE] == ""
            assert migration_data[CONF_MESSAGE_DEBUG_LOGGING] == True
            assert len(caplog.records) == 1

            config_flow = lennoxs30ConfigFlow()
            with patch.object(config_flow, "async_set_unique_id") as unique_id_mock:
                result = await config_flow.async_step_import(migration_data)
                assert result["title"] == "10.0.0.1"
                assert result["type"] == "create_entry"
                data = result["data"]
                assert data[CONF_SCAN_INTERVAL] == migration_data[CONF_SCAN_INTERVAL]
                assert CONF_EMAIL not in data
                assert CONF_PASSWORD not in data
                assert CONF_HOSTS not in data
                assert migration_data[CONF_HOST] == data[CONF_HOST]
                assert (
                    migration_data[CONF_FAST_POLL_INTERVAL]
                    == data[CONF_FAST_POLL_INTERVAL]
                )
                assert migration_data[CONF_CREATE_SENSORS] == data[CONF_CREATE_SENSORS]
                assert (
                    migration_data[CONF_ALLERGEN_DEFENDER_SWITCH]
                    == data[CONF_ALLERGEN_DEFENDER_SWITCH]
                )
                assert (
                    migration_data[CONF_CREATE_INVERTER_POWER]
                    == data[CONF_CREATE_INVERTER_POWER]
                )
                assert migration_data[CONF_PROTOCOL] == data[CONF_PROTOCOL]
                assert (
                    migration_data[CONF_PII_IN_MESSAGE_LOGS]
                    == data[CONF_PII_IN_MESSAGE_LOGS]
                )
                assert (
                    migration_data[CONF_MESSAGE_DEBUG_FILE]
                    == data[CONF_MESSAGE_DEBUG_FILE]
                )
                assert (
                    migration_data[CONF_MESSAGE_DEBUG_LOGGING]
                    == data[CONF_MESSAGE_DEBUG_LOGGING]
                )
                assert data[CONF_CLOUD_CONNECTION] == False
                assert data[CONF_APP_ID] == LENNOX_DEFAULT_LOCAL_APP_ID


@pytest.mark.asyncio
async def test_migrate_local_config_full(hass, caplog):
    config = {
        DOMAIN: {
            CONF_EMAIL: "myemail@email.com",
            CONF_PASSWORD: "mypassword",
            CONF_HOSTS: "10.0.0.1",
            CONF_FAST_POLL_INTERVAL: 0.75,
            CONF_ALLERGEN_DEFENDER_SWITCH: False,
            CONF_CREATE_SENSORS: False,
            CONF_CREATE_INVERTER_POWER: False,
            CONF_PROTOCOL: "https",
            CONF_PII_IN_MESSAGE_LOGS: False,
            CONF_MESSAGE_DEBUG_FILE: "",
            CONF_MESSAGE_DEBUG_LOGGING: True,
            CONF_APP_ID: "ha_prod",
            CONF_SCAN_INTERVAL: 3,
        }
    }
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        with patch(
            "custom_components.lennoxs30.create_migration_task"
        ) as mock_migration_task:
            await async_setup(hass, config)
            assert mock_migration_task.call_count == 1
            migration_data = mock_migration_task.call_args[0][1]
            assert migration_data[CONF_SCAN_INTERVAL] == 3
            assert CONF_EMAIL not in migration_data
            assert CONF_PASSWORD not in migration_data
            assert CONF_HOSTS not in migration_data
            assert migration_data[CONF_HOST] == "10.0.0.1"
            assert migration_data[CONF_FAST_POLL_INTERVAL] == 0.75
            assert migration_data[CONF_CREATE_SENSORS] == False
            assert migration_data[CONF_ALLERGEN_DEFENDER_SWITCH] == False
            assert migration_data[CONF_CREATE_INVERTER_POWER] == False
            assert migration_data[CONF_PROTOCOL] == "https"
            assert migration_data[CONF_PII_IN_MESSAGE_LOGS] == False
            assert migration_data[CONF_MESSAGE_DEBUG_FILE] == ""
            assert migration_data[CONF_MESSAGE_DEBUG_LOGGING] == True
            assert migration_data[CONF_APP_ID] == "ha_prod"
            assert len(caplog.records) == 1

            config_flow = lennoxs30ConfigFlow()
            with patch.object(config_flow, "async_set_unique_id") as unique_id_mock:
                result = await config_flow.async_step_import(migration_data)
                assert result["title"] == "10.0.0.1"
                assert result["type"] == "create_entry"
                data = result["data"]
                assert data[CONF_SCAN_INTERVAL] == migration_data[CONF_SCAN_INTERVAL]
                assert CONF_EMAIL not in data
                assert CONF_PASSWORD not in data
                assert CONF_HOSTS not in data
                assert migration_data[CONF_HOST] == data[CONF_HOST]
                assert (
                    migration_data[CONF_FAST_POLL_INTERVAL]
                    == data[CONF_FAST_POLL_INTERVAL]
                )
                assert migration_data[CONF_CREATE_SENSORS] == data[CONF_CREATE_SENSORS]
                assert (
                    migration_data[CONF_ALLERGEN_DEFENDER_SWITCH]
                    == data[CONF_ALLERGEN_DEFENDER_SWITCH]
                )
                assert (
                    migration_data[CONF_CREATE_INVERTER_POWER]
                    == data[CONF_CREATE_INVERTER_POWER]
                )
                assert migration_data[CONF_PROTOCOL] == data[CONF_PROTOCOL]
                assert (
                    migration_data[CONF_PII_IN_MESSAGE_LOGS]
                    == data[CONF_PII_IN_MESSAGE_LOGS]
                )
                assert (
                    migration_data[CONF_MESSAGE_DEBUG_FILE]
                    == data[CONF_MESSAGE_DEBUG_FILE]
                )
                assert (
                    migration_data[CONF_MESSAGE_DEBUG_LOGGING]
                    == data[CONF_MESSAGE_DEBUG_LOGGING]
                )
                assert data[CONF_CLOUD_CONNECTION] == False
                assert data[CONF_APP_ID] == "ha_prod"


@pytest.mark.asyncio
async def test_migrate_local_config_multiple(hass, caplog):
    config = {
        DOMAIN: {
            CONF_EMAIL: "myemail@email.com",
            CONF_PASSWORD: "mypassword",
            CONF_HOSTS: "10.0.0.1,10.0.0.2",
            CONF_FAST_POLL_INTERVAL: 0.75,
            CONF_ALLERGEN_DEFENDER_SWITCH: False,
            CONF_CREATE_SENSORS: False,
            CONF_CREATE_INVERTER_POWER: False,
            CONF_PROTOCOL: "https",
            CONF_PII_IN_MESSAGE_LOGS: False,
            CONF_MESSAGE_DEBUG_FILE: "",
            CONF_MESSAGE_DEBUG_LOGGING: True,
        }
    }
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        with patch(
            "custom_components.lennoxs30.create_migration_task"
        ) as mock_migration_task:
            await async_setup(hass, config)
            assert mock_migration_task.call_count == 2
            migration_data = mock_migration_task.mock_calls[0][1][1]
            assert migration_data[CONF_SCAN_INTERVAL] == DEFAULT_LOCAL_POLL_INTERVAL
            assert CONF_EMAIL not in migration_data
            assert CONF_PASSWORD not in migration_data
            assert CONF_HOSTS not in migration_data
            assert migration_data[CONF_HOST] == "10.0.0.1"
            assert migration_data[CONF_FAST_POLL_INTERVAL] == 0.75
            assert migration_data[CONF_CREATE_SENSORS] == False
            assert migration_data[CONF_ALLERGEN_DEFENDER_SWITCH] == False
            assert migration_data[CONF_CREATE_INVERTER_POWER] == False
            assert migration_data[CONF_PROTOCOL] == "https"
            assert migration_data[CONF_PII_IN_MESSAGE_LOGS] == False
            assert migration_data[CONF_MESSAGE_DEBUG_FILE] == ""
            assert migration_data[CONF_MESSAGE_DEBUG_LOGGING] == True

            migration_data = mock_migration_task.mock_calls[1][1][1]
            assert migration_data[CONF_SCAN_INTERVAL] == DEFAULT_LOCAL_POLL_INTERVAL
            assert CONF_EMAIL not in migration_data
            assert CONF_PASSWORD not in migration_data
            assert CONF_HOSTS not in migration_data
            assert migration_data[CONF_HOST] == "10.0.0.2"
            assert migration_data[CONF_FAST_POLL_INTERVAL] == 0.75
            assert migration_data[CONF_CREATE_SENSORS] == False
            assert migration_data[CONF_ALLERGEN_DEFENDER_SWITCH] == False
            assert migration_data[CONF_CREATE_INVERTER_POWER] == False
            assert migration_data[CONF_PROTOCOL] == "https"
            assert migration_data[CONF_PII_IN_MESSAGE_LOGS] == False
            assert migration_data[CONF_MESSAGE_DEBUG_FILE] == ""
            assert migration_data[CONF_MESSAGE_DEBUG_LOGGING] == True

            assert len(caplog.records) == 1


@pytest.mark.asyncio
async def test_migrate_cloud_config_min(hass, caplog):
    config = {
        DOMAIN: {
            CONF_EMAIL: "myemail@email.com",
            CONF_PASSWORD: "mypassword",
            CONF_HOSTS: "Cloud",
            CONF_FAST_POLL_INTERVAL: 0.75,
            CONF_ALLERGEN_DEFENDER_SWITCH: False,
            CONF_CREATE_SENSORS: False,
            CONF_CREATE_INVERTER_POWER: False,
            CONF_PROTOCOL: "https",
            CONF_PII_IN_MESSAGE_LOGS: False,
            CONF_MESSAGE_DEBUG_FILE: "",
            CONF_MESSAGE_DEBUG_LOGGING: True,
        }
    }
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        with patch(
            "custom_components.lennoxs30.create_migration_task"
        ) as mock_migration_task:
            await async_setup(hass, config)
            assert mock_migration_task.call_count == 1
            migration_data = mock_migration_task.call_args[0][1]
            assert migration_data[CONF_SCAN_INTERVAL] == DEFAULT_POLL_INTERVAL
            assert CONF_HOST not in migration_data
            assert CONF_HOSTS not in migration_data
            assert CONF_CREATE_INVERTER_POWER not in migration_data
            assert migration_data[CONF_EMAIL] == "myemail@email.com"
            assert migration_data[CONF_PASSWORD] == "mypassword"
            assert migration_data[CONF_FAST_POLL_INTERVAL] == 0.75
            assert migration_data[CONF_CREATE_SENSORS] == False
            assert migration_data[CONF_ALLERGEN_DEFENDER_SWITCH] == False
            assert migration_data[CONF_PROTOCOL] == "https"
            assert migration_data[CONF_PII_IN_MESSAGE_LOGS] == False
            assert migration_data[CONF_MESSAGE_DEBUG_FILE] == ""
            assert migration_data[CONF_MESSAGE_DEBUG_LOGGING] == True
            config_flow = lennoxs30ConfigFlow()
            with patch.object(config_flow, "async_set_unique_id") as unique_id_mock:
                result = await config_flow.async_step_import(migration_data)
                assert result["title"] == redact_email(migration_data[CONF_EMAIL])
                assert result["type"] == "create_entry"
                data = result["data"]
                assert data[CONF_SCAN_INTERVAL] == migration_data[CONF_SCAN_INTERVAL]
                assert CONF_HOST not in data
                assert CONF_CREATE_INVERTER_POWER not in data
                assert migration_data[CONF_EMAIL] == data[CONF_EMAIL]
                assert migration_data[CONF_PASSWORD] == data[CONF_PASSWORD]
                assert (
                    migration_data[CONF_FAST_POLL_INTERVAL]
                    == data[CONF_FAST_POLL_INTERVAL]
                )
                assert migration_data[CONF_CREATE_SENSORS] == data[CONF_CREATE_SENSORS]
                assert (
                    migration_data[CONF_ALLERGEN_DEFENDER_SWITCH]
                    == data[CONF_ALLERGEN_DEFENDER_SWITCH]
                )
                assert migration_data[CONF_PROTOCOL] == data[CONF_PROTOCOL]
                assert (
                    migration_data[CONF_PII_IN_MESSAGE_LOGS]
                    == data[CONF_PII_IN_MESSAGE_LOGS]
                )
                assert (
                    migration_data[CONF_MESSAGE_DEBUG_FILE]
                    == data[CONF_MESSAGE_DEBUG_FILE]
                )
                assert (
                    migration_data[CONF_MESSAGE_DEBUG_LOGGING]
                    == data[CONF_MESSAGE_DEBUG_LOGGING]
                )
                assert data[CONF_CLOUD_CONNECTION] == True
                assert data[CONF_APP_ID] == LENNOX_DEFAULT_CLOUD_APP_ID


@pytest.mark.asyncio
async def test_migrate_cloud_config_full(hass, caplog):
    config = {
        DOMAIN: {
            CONF_EMAIL: "myemail@email.com",
            CONF_PASSWORD: "mypassword",
            CONF_HOSTS: "Cloud",
            CONF_FAST_POLL_INTERVAL: 0.75,
            CONF_ALLERGEN_DEFENDER_SWITCH: False,
            CONF_CREATE_SENSORS: False,
            CONF_CREATE_INVERTER_POWER: False,
            CONF_PROTOCOL: "https",
            CONF_PII_IN_MESSAGE_LOGS: False,
            CONF_MESSAGE_DEBUG_FILE: "",
            CONF_MESSAGE_DEBUG_LOGGING: True,
            CONF_SCAN_INTERVAL: 10,
            CONF_APP_ID: "thisismyapp_id",
        }
    }
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        with patch(
            "custom_components.lennoxs30.create_migration_task"
        ) as mock_migration_task:
            await async_setup(hass, config)
            assert mock_migration_task.call_count == 1
            migration_data = mock_migration_task.call_args[0][1]
            assert migration_data[CONF_SCAN_INTERVAL] == DEFAULT_POLL_INTERVAL
            assert CONF_HOST not in migration_data
            assert CONF_HOSTS not in migration_data
            assert CONF_CREATE_INVERTER_POWER not in migration_data
            assert migration_data[CONF_EMAIL] == "myemail@email.com"
            assert migration_data[CONF_PASSWORD] == "mypassword"
            assert migration_data[CONF_FAST_POLL_INTERVAL] == 0.75
            assert migration_data[CONF_CREATE_SENSORS] == False
            assert migration_data[CONF_ALLERGEN_DEFENDER_SWITCH] == False
            assert migration_data[CONF_PROTOCOL] == "https"
            assert migration_data[CONF_PII_IN_MESSAGE_LOGS] == False
            assert migration_data[CONF_MESSAGE_DEBUG_FILE] == ""
            assert migration_data[CONF_MESSAGE_DEBUG_LOGGING] == True
            config_flow = lennoxs30ConfigFlow()
            with patch.object(config_flow, "async_set_unique_id") as unique_id_mock:
                result = await config_flow.async_step_import(migration_data)
                assert result["title"] == redact_email(migration_data[CONF_EMAIL])
                assert result["type"] == "create_entry"
                data = result["data"]
                assert data[CONF_SCAN_INTERVAL] == migration_data[CONF_SCAN_INTERVAL]
                assert CONF_HOST not in data
                assert CONF_CREATE_INVERTER_POWER not in data
                assert migration_data[CONF_EMAIL] == data[CONF_EMAIL]
                assert migration_data[CONF_PASSWORD] == data[CONF_PASSWORD]
                assert (
                    migration_data[CONF_FAST_POLL_INTERVAL]
                    == data[CONF_FAST_POLL_INTERVAL]
                )
                assert migration_data[CONF_CREATE_SENSORS] == data[CONF_CREATE_SENSORS]
                assert (
                    migration_data[CONF_ALLERGEN_DEFENDER_SWITCH]
                    == data[CONF_ALLERGEN_DEFENDER_SWITCH]
                )
                assert migration_data[CONF_PROTOCOL] == data[CONF_PROTOCOL]
                assert (
                    migration_data[CONF_PII_IN_MESSAGE_LOGS]
                    == data[CONF_PII_IN_MESSAGE_LOGS]
                )
                assert (
                    migration_data[CONF_MESSAGE_DEBUG_FILE]
                    == data[CONF_MESSAGE_DEBUG_FILE]
                )
                assert (
                    migration_data[CONF_MESSAGE_DEBUG_LOGGING]
                    == data[CONF_MESSAGE_DEBUG_LOGGING]
                )
                assert data[CONF_CLOUD_CONNECTION] == True
                assert data[CONF_APP_ID] == "thisismyapp_id"


@pytest.mark.asyncio
async def test_upgrade_config_v1_v2(hass, caplog):
    data = {
        "cloud_connection": False,
        "host": "192.168.1.93",
        "app_id": "homeassistant",
        "create_sensors": True,
        "allergen_defender_switch": False,
        "create_inverter_power": False,
        "protocol": "https",
        "scan_interval": 1,
        "fast_scan_interval": 0.75,
        "init_wait_time": 30,
        "pii_in_message_logs": False,
        "message_debug_logging": True,
        "log_messages_to_file": False,
        "message_debug_file": "",
    }

    config_entry = config_entries.ConfigEntry(1, DOMAIN, "Test", data, "my_source")
    with patch.object(hass.config_entries, "async_update_entry") as update_entry:
        await async_migrate_entry(hass, config_entry)
        assert update_entry.call_count == 1
        new_data = update_entry.call_args_list[0].kwargs["data"]
        assert config_entry.version == 2
        assert new_data["cloud_connection"] == False
        assert new_data["host"] == "192.168.1.93"
        assert new_data["app_id"] == "homeassistant"
        assert new_data["create_sensors"] == True
        assert new_data["allergen_defender_switch"] == False
        assert new_data["create_inverter_power"] == False
        assert new_data["protocol"] == "https"
        assert new_data["scan_interval"] == 1
        assert new_data["fast_scan_interval"] == 0.75
        assert new_data["init_wait_time"] == 30
        assert new_data["pii_in_message_logs"] == False
        assert new_data["message_debug_logging"] == True
        assert new_data["log_messages_to_file"] == False
        assert new_data["message_debug_file"] == ""
        assert new_data["fast_scan_count"] == 10
        assert new_data["timeout"] == 30

    data = {
        "cloud_connection": True,
        "email": "pete@pete.com",
        "password": "secret",
        "app_id": "homeassistant",
        "create_sensors": True,
        "allergen_defender_switch": False,
        "create_inverter_power": False,
        "protocol": "https",
        "scan_interval": 1,
        "fast_scan_interval": 0.75,
        "init_wait_time": 30,
        "pii_in_message_logs": False,
        "message_debug_logging": True,
        "log_messages_to_file": False,
        "message_debug_file": "",
    }

    config_entry = config_entries.ConfigEntry(1, DOMAIN, "Test", data, "my_source")
    with patch.object(hass.config_entries, "async_update_entry") as update_entry:
        await async_migrate_entry(hass, config_entry)
        assert update_entry.call_count == 1
        new_data = update_entry.call_args_list[0].kwargs["data"]
        assert config_entry.version == 2
        assert new_data["cloud_connection"] == True
        assert new_data["email"] == "pete@pete.com"
        assert new_data["password"] == "secret"
        assert new_data["app_id"] == "homeassistant"
        assert new_data["create_sensors"] == True
        assert new_data["allergen_defender_switch"] == False
        assert new_data["create_inverter_power"] == False
        assert new_data["protocol"] == "https"
        assert new_data["scan_interval"] == 1
        assert new_data["fast_scan_interval"] == 0.75
        assert new_data["init_wait_time"] == 30
        assert new_data["pii_in_message_logs"] == False
        assert new_data["message_debug_logging"] == True
        assert new_data["log_messages_to_file"] == False
        assert new_data["message_debug_file"] == ""
        assert new_data["fast_scan_count"] == 10
        assert new_data["timeout"] == DEFAULT_CLOUD_TIMEOUT
