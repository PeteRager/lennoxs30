"""Test config flow."""
from optparse import Option
from re import T
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from lennoxs30api.s30exception import S30Exception, EC_LOGIN, EC_COMMS_ERROR

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
    CONF_TIMEOUT,
)

import pytest

from homeassistant import config_entries, data_entry_flow
from custom_components.lennoxs30.config_flow import (
    OptionsFlowHandler,
    host_valid,
    lennoxs30ConfigFlow,
    STEP_CLOUD,
    STEP_LOCAL,
    STEP_ONE,
)
from custom_components.lennoxs30.const import (
    CONF_ALLERGEN_DEFENDER_SWITCH,
    CONF_CLOUD_CONNECTION,
    CONF_CREATE_INVERTER_POWER,
    CONF_CREATE_SENSORS,
    CONF_FAST_POLL_INTERVAL,
    CONF_LOCAL_CONNECTION,
    CONF_MESSAGE_DEBUG_FILE,
    CONF_MESSAGE_DEBUG_LOGGING,
    CONF_PII_IN_MESSAGE_LOGS,
    CONF_APP_ID,
    DEFAULT_CLOUD_TIMEOUT,
    LENNOX_DEFAULT_CLOUD_APP_ID,
    LENNOX_DEFAULT_LOCAL_APP_ID,
    CONF_FAST_POLL_COUNT,
    DEFAULT_LOCAL_TIMEOUT,
    CONF_INIT_WAIT_TIME,
    CONF_LOG_MESSAGES_TO_FILE,
    CONF_CREATE_DIAGNOSTICS_SENSORS,
    CONF_CREATE_PARAMETERS,
)


# from tests.common import MockConfigEntry

from custom_components.lennoxs30 import (
    DEFAULT_LOCAL_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    Manager,
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
        with patch("custom_components.lennoxs30.create_migration_task") as mock_migration_task:
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
            assert migration_data[CONF_SCAN_INTERVAL] == DEFAULT_LOCAL_POLL_INTERVAL
            assert migration_data[CONF_FAST_POLL_COUNT] == 10
            assert migration_data[CONF_TIMEOUT] == DEFAULT_LOCAL_TIMEOUT

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
                assert migration_data[CONF_FAST_POLL_INTERVAL] == data[CONF_FAST_POLL_INTERVAL]
                assert migration_data[CONF_CREATE_SENSORS] == data[CONF_CREATE_SENSORS]
                assert migration_data[CONF_ALLERGEN_DEFENDER_SWITCH] == data[CONF_ALLERGEN_DEFENDER_SWITCH]
                assert migration_data[CONF_CREATE_INVERTER_POWER] == data[CONF_CREATE_INVERTER_POWER]
                assert migration_data[CONF_PROTOCOL] == data[CONF_PROTOCOL]
                assert migration_data[CONF_PII_IN_MESSAGE_LOGS] == data[CONF_PII_IN_MESSAGE_LOGS]
                assert migration_data[CONF_MESSAGE_DEBUG_FILE] == data[CONF_MESSAGE_DEBUG_FILE]
                assert migration_data[CONF_MESSAGE_DEBUG_LOGGING] == data[CONF_MESSAGE_DEBUG_LOGGING]
                assert data[CONF_CLOUD_CONNECTION] == False
                assert data[CONF_APP_ID] == LENNOX_DEFAULT_LOCAL_APP_ID
                assert migration_data[CONF_SCAN_INTERVAL] == data[CONF_SCAN_INTERVAL]
                assert migration_data[CONF_FAST_POLL_COUNT] == data[CONF_FAST_POLL_COUNT]
                assert migration_data[CONF_TIMEOUT] == data[CONF_TIMEOUT]


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
        with patch("custom_components.lennoxs30.create_migration_task") as mock_migration_task:
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
            assert migration_data[CONF_FAST_POLL_COUNT] == 10
            assert migration_data[CONF_TIMEOUT] == DEFAULT_LOCAL_TIMEOUT

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
                assert migration_data[CONF_FAST_POLL_INTERVAL] == data[CONF_FAST_POLL_INTERVAL]
                assert migration_data[CONF_CREATE_SENSORS] == data[CONF_CREATE_SENSORS]
                assert migration_data[CONF_ALLERGEN_DEFENDER_SWITCH] == data[CONF_ALLERGEN_DEFENDER_SWITCH]
                assert migration_data[CONF_CREATE_INVERTER_POWER] == data[CONF_CREATE_INVERTER_POWER]
                assert migration_data[CONF_PROTOCOL] == data[CONF_PROTOCOL]
                assert migration_data[CONF_PII_IN_MESSAGE_LOGS] == data[CONF_PII_IN_MESSAGE_LOGS]
                assert migration_data[CONF_MESSAGE_DEBUG_FILE] == data[CONF_MESSAGE_DEBUG_FILE]
                assert migration_data[CONF_MESSAGE_DEBUG_LOGGING] == data[CONF_MESSAGE_DEBUG_LOGGING]
                assert data[CONF_CLOUD_CONNECTION] == False
                assert data[CONF_APP_ID] == "ha_prod"
                assert migration_data[CONF_SCAN_INTERVAL] == data[CONF_SCAN_INTERVAL]
                assert migration_data[CONF_FAST_POLL_COUNT] == data[CONF_FAST_POLL_COUNT]
                assert migration_data[CONF_TIMEOUT] == data[CONF_TIMEOUT]


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
        with patch("custom_components.lennoxs30.create_migration_task") as mock_migration_task:
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
            assert migration_data[CONF_SCAN_INTERVAL] == DEFAULT_LOCAL_POLL_INTERVAL
            assert migration_data[CONF_FAST_POLL_COUNT] == 10
            assert migration_data[CONF_TIMEOUT] == DEFAULT_LOCAL_TIMEOUT

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
            assert migration_data[CONF_SCAN_INTERVAL] == DEFAULT_LOCAL_POLL_INTERVAL
            assert migration_data[CONF_FAST_POLL_COUNT] == 10
            assert migration_data[CONF_TIMEOUT] == DEFAULT_LOCAL_TIMEOUT

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
        with patch("custom_components.lennoxs30.create_migration_task") as mock_migration_task:
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
            assert migration_data[CONF_SCAN_INTERVAL] == DEFAULT_POLL_INTERVAL
            assert migration_data[CONF_FAST_POLL_COUNT] == 10
            assert migration_data[CONF_TIMEOUT] == DEFAULT_CLOUD_TIMEOUT

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
                assert migration_data[CONF_FAST_POLL_INTERVAL] == data[CONF_FAST_POLL_INTERVAL]
                assert migration_data[CONF_CREATE_SENSORS] == data[CONF_CREATE_SENSORS]
                assert migration_data[CONF_ALLERGEN_DEFENDER_SWITCH] == data[CONF_ALLERGEN_DEFENDER_SWITCH]
                assert migration_data[CONF_PROTOCOL] == data[CONF_PROTOCOL]
                assert migration_data[CONF_PII_IN_MESSAGE_LOGS] == data[CONF_PII_IN_MESSAGE_LOGS]
                assert migration_data[CONF_MESSAGE_DEBUG_FILE] == data[CONF_MESSAGE_DEBUG_FILE]
                assert migration_data[CONF_MESSAGE_DEBUG_LOGGING] == data[CONF_MESSAGE_DEBUG_LOGGING]
                assert data[CONF_CLOUD_CONNECTION] == True
                assert data[CONF_APP_ID] == LENNOX_DEFAULT_CLOUD_APP_ID
                assert migration_data[CONF_SCAN_INTERVAL] == data[CONF_SCAN_INTERVAL]
                assert migration_data[CONF_FAST_POLL_COUNT] == data[CONF_FAST_POLL_COUNT]
                assert migration_data[CONF_TIMEOUT] == data[CONF_TIMEOUT]


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
        with patch("custom_components.lennoxs30.create_migration_task") as mock_migration_task:
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
            assert migration_data[CONF_FAST_POLL_COUNT] == 10
            assert migration_data[CONF_TIMEOUT] == DEFAULT_CLOUD_TIMEOUT

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
                assert migration_data[CONF_FAST_POLL_INTERVAL] == data[CONF_FAST_POLL_INTERVAL]
                assert migration_data[CONF_CREATE_SENSORS] == data[CONF_CREATE_SENSORS]
                assert migration_data[CONF_ALLERGEN_DEFENDER_SWITCH] == data[CONF_ALLERGEN_DEFENDER_SWITCH]
                assert migration_data[CONF_PROTOCOL] == data[CONF_PROTOCOL]
                assert migration_data[CONF_PII_IN_MESSAGE_LOGS] == data[CONF_PII_IN_MESSAGE_LOGS]
                assert migration_data[CONF_MESSAGE_DEBUG_FILE] == data[CONF_MESSAGE_DEBUG_FILE]
                assert migration_data[CONF_MESSAGE_DEBUG_LOGGING] == data[CONF_MESSAGE_DEBUG_LOGGING]
                assert data[CONF_CLOUD_CONNECTION] == True
                assert data[CONF_APP_ID] == "thisismyapp_id"
                assert migration_data[CONF_SCAN_INTERVAL] == data[CONF_SCAN_INTERVAL]
                assert migration_data[CONF_FAST_POLL_COUNT] == data[CONF_FAST_POLL_COUNT]
                assert migration_data[CONF_TIMEOUT] == data[CONF_TIMEOUT]


@pytest.mark.asyncio
async def test_upgrade_config_v1(hass, caplog):
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
        assert config_entry.version == 4
        assert new_data["cloud_connection"] == False
        assert new_data["host"] == "192.168.1.93"
        assert new_data["app_id"] == "homeassistant"
        assert new_data["create_sensors"] == True
        assert new_data["allergen_defender_switch"] == False
        assert new_data["create_inverter_power"] == False
        assert new_data["create_diagnostic_sensors"] == False
        assert new_data["create_parameters"] == False
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
        assert config_entry.version == 4
        assert new_data["cloud_connection"] == True
        assert new_data["email"] == "pete@pete.com"
        assert new_data["password"] == "secret"
        assert new_data["app_id"] == "homeassistant"
        assert new_data["create_sensors"] == True
        assert new_data["allergen_defender_switch"] == False
        assert new_data["create_inverter_power"] == False
        assert new_data["create_diagnostic_sensors"] == False
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


@pytest.mark.asyncio
async def test_upgrade_config_v2(hass, caplog):
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
        "fast_scan_count": 10,
        "timeout": 30,
    }

    config_entry = config_entries.ConfigEntry(1, DOMAIN, "Test", data, "my_source")
    with patch.object(hass.config_entries, "async_update_entry") as update_entry:
        await async_migrate_entry(hass, config_entry)
        assert update_entry.call_count == 1
        new_data = update_entry.call_args_list[0].kwargs["data"]
        assert config_entry.version == 4
        assert new_data["cloud_connection"] == False
        assert new_data["host"] == "192.168.1.93"
        assert new_data["app_id"] == "homeassistant"
        assert new_data["create_sensors"] == True
        assert new_data["allergen_defender_switch"] == False
        assert new_data["create_inverter_power"] == False
        assert new_data["create_parameters"] == False
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

        assert new_data["create_diagnostic_sensors"] == False

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
        "fast_scan_count": 10,
        "timeout": 30,
    }

    config_entry = config_entries.ConfigEntry(1, DOMAIN, "Test", data, "my_source")
    with patch.object(hass.config_entries, "async_update_entry") as update_entry:
        await async_migrate_entry(hass, config_entry)
        assert update_entry.call_count == 1
        new_data = update_entry.call_args_list[0].kwargs["data"]
        assert config_entry.version == 4
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

        assert new_data["create_diagnostic_sensors"] == False


@pytest.mark.asyncio
async def test_upgrade_config_v3(hass, caplog):
    data = {
        "cloud_connection": False,
        "host": "192.168.1.93",
        "app_id": "homeassistant",
        "create_sensors": True,
        "allergen_defender_switch": False,
        "create_inverter_power": False,
        "create_diagnostic_sensors": False,
        "protocol": "https",
        "scan_interval": 1,
        "fast_scan_interval": 0.75,
        "init_wait_time": 30,
        "pii_in_message_logs": False,
        "message_debug_logging": True,
        "log_messages_to_file": False,
        "message_debug_file": "",
        "fast_scan_count": 10,
        "timeout": 30,
    }

    config_entry = config_entries.ConfigEntry(1, DOMAIN, "Test", data, "my_source")
    with patch.object(hass.config_entries, "async_update_entry") as update_entry:
        await async_migrate_entry(hass, config_entry)
        assert update_entry.call_count == 1
        new_data = update_entry.call_args_list[0].kwargs["data"]
        assert config_entry.version == 4
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
        assert new_data["create_diagnostic_sensors"] == False

        assert new_data["create_parameters"] == False

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
        "fast_scan_count": 10,
        "timeout": 30,
    }

    config_entry = config_entries.ConfigEntry(1, DOMAIN, "Test", data, "my_source")
    with patch.object(hass.config_entries, "async_update_entry") as update_entry:
        await async_migrate_entry(hass, config_entry)
        assert update_entry.call_count == 1
        new_data = update_entry.call_args_list[0].kwargs["data"]
        assert config_entry.version == 4
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
        assert new_data["create_diagnostic_sensors"] == False


def test_config_flow_host_valid(hass, caplog):
    assert host_valid("10.23.23.45") == True
    assert host_valid("10.23.23.45:9191") == True
    assert host_valid("localhost") == True
    assert host_valid("mydomain.google.com") == True
    assert host_valid("mydomain.google.com:444") == True
    assert host_valid("<>DDDD>") == False


def test_lennoxS30ConfigFlow(manager: Manager, hass, caplog):
    cf = lennoxs30ConfigFlow()
    cf.hass = hass
    assert cf._host_in_configuration_exists("localhost") == False

    schema = cf.get_advanced_schema(is_cloud=False)
    si = schema.schema["scan_interval"]
    si.required == False
    v0: vol.Coerce = si.validators[0]
    assert isinstance(v0, vol.Coerce)
    assert v0.type_name == "int"
    v1: vol.Range = si.validators[1]
    assert v1.min == 1
    assert v1.max == 300

    si = schema.schema[CONF_FAST_POLL_INTERVAL]
    si.required == False
    v0: vol.Coerce = si.validators[0]
    assert isinstance(v0, vol.Coerce)
    assert v0.type_name == "float"
    v1: vol.Range = si.validators[1]
    assert v1.min == 0.25
    assert v1.max == 300.0

    si = schema.schema[CONF_FAST_POLL_COUNT]
    si.required == False
    v0: vol.Coerce = si.validators[0]
    assert isinstance(v0, vol.Coerce)
    assert v0.type_name == "int"
    v1: vol.Range = si.validators[1]
    assert v1.min == 1
    assert v1.max == 100

    si = schema.schema[CONF_INIT_WAIT_TIME]
    si.required == False
    v0: vol.Coerce = si.validators[0]
    assert isinstance(v0, vol.Coerce)
    assert v0.type_name == "int"
    v1: vol.Range = si.validators[1]
    assert v1.min == 1
    assert v1.max == 300

    si = schema.schema[CONF_TIMEOUT]
    si.required == False
    v0: vol.Coerce = si.validators[0]
    assert isinstance(v0, vol.Coerce)
    assert v0.type_name == "int"
    v1: vol.Range = si.validators[1]
    assert v1.min == 15
    assert v1.max == 300

    si = schema.schema[CONF_PII_IN_MESSAGE_LOGS]
    assert si == cv.boolean

    si = schema.schema[CONF_MESSAGE_DEBUG_LOGGING]
    assert si == cv.boolean
    si = schema.schema[CONF_LOG_MESSAGES_TO_FILE]
    assert si == cv.boolean
    si = schema.schema[CONF_MESSAGE_DEBUG_FILE]
    assert si == cv.string

    # TODO - don't know how to validate the default values.

    schema = cf.get_advanced_schema(is_cloud=True)
    si = schema.schema["scan_interval"]
    si.required == False
    v0: vol.Coerce = si.validators[0]
    assert isinstance(v0, vol.Coerce)
    assert v0.type_name == "int"
    v1: vol.Range = si.validators[1]
    assert v1.min == 1
    assert v1.max == 300

    si = schema.schema[CONF_FAST_POLL_INTERVAL]
    si.required == False
    v0: vol.Coerce = si.validators[0]
    assert isinstance(v0, vol.Coerce)
    assert v0.type_name == "float"
    v1: vol.Range = si.validators[1]
    assert v1.min == 0.25
    assert v1.max == 300.0

    si = schema.schema[CONF_FAST_POLL_COUNT]
    si.required == False
    v0: vol.Coerce = si.validators[0]
    assert isinstance(v0, vol.Coerce)
    assert v0.type_name == "int"
    v1: vol.Range = si.validators[1]
    assert v1.min == 1
    assert v1.max == 100

    si = schema.schema[CONF_INIT_WAIT_TIME]
    si.required == False
    v0: vol.Coerce = si.validators[0]
    assert isinstance(v0, vol.Coerce)
    assert v0.type_name == "int"
    v1: vol.Range = si.validators[1]
    assert v1.min == 1
    assert v1.max == 300

    si = schema.schema[CONF_TIMEOUT]
    si.required == False
    v0: vol.Coerce = si.validators[0]
    assert isinstance(v0, vol.Coerce)
    assert v0.type_name == "int"
    v1: vol.Range = si.validators[1]
    assert v1.min == 15
    assert v1.max == 300

    si = schema.schema[CONF_PII_IN_MESSAGE_LOGS]
    assert si == cv.boolean

    si = schema.schema[CONF_MESSAGE_DEBUG_LOGGING]
    assert si == cv.boolean
    si = schema.schema[CONF_LOG_MESSAGES_TO_FILE]
    assert si == cv.boolean
    si = schema.schema[CONF_MESSAGE_DEBUG_FILE]
    assert si == cv.string


@pytest.mark.asyncio
async def test_lennoxS30ConfigFlow_async_step_user(manager: Manager, hass, caplog):
    cf = lennoxs30ConfigFlow()
    cf.hass = hass
    res = await cf.async_step_user(user_input=None)
    res["type"] == "form"
    res["step_id"] == "user"
    res["data_schema"] == STEP_ONE
    len(res["errors"]) == 0

    user_input: dict = {}
    user_input[CONF_CLOUD_CONNECTION] = True
    user_input[CONF_LOCAL_CONNECTION] = True
    res = await cf.async_step_user(user_input=user_input)
    res["type"] == "form"
    res["step_id"] == "user"
    res["data_schema"] == STEP_ONE
    len(res["errors"]) == 1
    assert res["errors"][CONF_LOCAL_CONNECTION] == "select_cloud_or_local"

    user_input: dict = {}
    user_input[CONF_CLOUD_CONNECTION] = False
    user_input[CONF_LOCAL_CONNECTION] = False
    res = await cf.async_step_user(user_input=user_input)
    res["type"] == "form"
    res["step_id"] == "user"
    res["data_schema"] == STEP_ONE
    len(res["errors"]) == 1
    assert res["errors"][CONF_LOCAL_CONNECTION] == "select_cloud_or_local"

    user_input: dict = {}
    user_input[CONF_CLOUD_CONNECTION] = True
    user_input[CONF_LOCAL_CONNECTION] = False
    res = await cf.async_step_user(user_input=user_input)
    res["type"] == "form"
    res["step_id"] == "cloud"
    res["data_schema"] == STEP_CLOUD
    len(res["errors"]) == 0
    len(cf.config_input) == 1
    cf.config_input[CONF_CLOUD_CONNECTION] == True

    user_input: dict = {}
    user_input[CONF_CLOUD_CONNECTION] = False
    user_input[CONF_LOCAL_CONNECTION] = True
    res = await cf.async_step_user(user_input=user_input)
    res["type"] == "form"
    res["step_id"] == "local"
    res["data_schema"] == STEP_LOCAL
    len(res["errors"]) == 0
    len(cf.config_input) == 1
    assert cf.config_input[CONF_CLOUD_CONNECTION] == False


@pytest.mark.asyncio
async def test_lennoxS30ConfigFlow_async_step_cloud(manager: Manager, hass, caplog):
    cf = lennoxs30ConfigFlow()
    cf.hass = hass

    with patch.object(cf, "async_set_unique_id") as async_set_unique_id:
        with patch.object(cf, "try_to_connect") as try_to_connect:
            user_input: dict = {}
            user_input[CONF_EMAIL] = "pete.rage@rage.com"
            user_input[CONF_PASSWORD] = "secret"
            user_input[CONF_APP_ID] = "ha_prod"
            user_input[CONF_CREATE_SENSORS] = True
            user_input[CONF_ALLERGEN_DEFENDER_SWITCH] = True
            cf.config_input = {}
            cf.config_input[CONF_CLOUD_CONNECTION] = True
            res = await cf.async_step_cloud(user_input=user_input)
            assert len(cf.config_input) == 6
            assert cf.config_input[CONF_CLOUD_CONNECTION] == True
            assert cf.config_input[CONF_EMAIL] == "pete.rage@rage.com"
            assert cf.config_input[CONF_PASSWORD] == "secret"
            assert cf.config_input[CONF_APP_ID] == "ha_prod"
            assert cf.config_input[CONF_CREATE_SENSORS] == True
            assert cf.config_input[CONF_ALLERGEN_DEFENDER_SWITCH] == True

            assert try_to_connect.call_count == 1
            assert async_set_unique_id.call_count == 1
            assert async_set_unique_id.call_args[0][0] == "lennoxs30_pete.rage@rage.com"
            res["type"] == "form"
            res["step_id"] == "advanced"
            res["data_schema"] == cf.get_advanced_schema(True)
            len(res["errors"]) == 0

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(cf, "async_set_unique_id") as async_set_unique_id:
            with patch.object(cf, "try_to_connect") as try_to_connect:
                try_to_connect.side_effect = S30Exception("This is the error", EC_LOGIN, 100)
                user_input: dict = {}
                user_input[CONF_EMAIL] = "pete.rage@rage.com"
                user_input[CONF_PASSWORD] = "secret"
                user_input[CONF_APP_ID] = "ha_prod"
                user_input[CONF_CREATE_SENSORS] = True
                user_input[CONF_ALLERGEN_DEFENDER_SWITCH] = True
                cf.config_input = {}
                cf.config_input[CONF_CLOUD_CONNECTION] = True
                res = await cf.async_step_cloud(user_input=user_input)
                assert len(cf.config_input) == 1
                res["type"] == "form"
                res["step_id"] == "cloud"
                res["data_schema"] == STEP_CLOUD
                len(res["errors"]) == 1
                res["errors"]["base"] = "unable_to_connect_login"
                assert len(caplog.messages) == 1
                assert "This is the error" in caplog.messages[0]

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(cf, "async_set_unique_id") as async_set_unique_id:
            with patch.object(cf, "try_to_connect") as try_to_connect:
                try_to_connect.side_effect = S30Exception("This is the error", EC_COMMS_ERROR, 100)
                user_input: dict = {}
                user_input[CONF_EMAIL] = "pete.rage@rage.com"
                user_input[CONF_PASSWORD] = "secret"
                user_input[CONF_APP_ID] = "ha_prod"
                user_input[CONF_CREATE_SENSORS] = True
                user_input[CONF_ALLERGEN_DEFENDER_SWITCH] = True
                cf.config_input = {}
                cf.config_input[CONF_CLOUD_CONNECTION] = True
                res = await cf.async_step_cloud(user_input=user_input)
                assert len(cf.config_input) == 1
                res["type"] == "form"
                res["step_id"] == "cloud"
                res["data_schema"] == STEP_CLOUD
                len(res["errors"]) == 1
                res["errors"]["base"] = "unable_to_connect_cloud"
                assert len(caplog.messages) == 1
                assert "This is the error" in caplog.messages[0]


@pytest.mark.asyncio
async def test_lennoxS30ConfigFlow_async_step_local(manager: Manager, hass, caplog):
    cf = lennoxs30ConfigFlow()
    cf.hass = hass

    with patch.object(cf, "async_set_unique_id") as async_set_unique_id:
        with patch.object(cf, "try_to_connect") as try_to_connect:
            user_input: dict = {}
            user_input[CONF_HOST] = "10.11.12.13:4444"
            user_input[CONF_APP_ID] = "ha_prod"
            user_input[CONF_CREATE_SENSORS] = True
            user_input[CONF_ALLERGEN_DEFENDER_SWITCH] = True
            user_input[CONF_CREATE_INVERTER_POWER] = True
            user_input[CONF_CREATE_DIAGNOSTICS_SENSORS] = True
            user_input[CONF_CREATE_PARAMETERS] = True
            user_input[CONF_PROTOCOL] = "https"
            cf.config_input = {}
            cf.config_input[CONF_CLOUD_CONNECTION] = False
            res = await cf.async_step_local(user_input=user_input)
            assert len(cf.config_input) == 9
            assert cf.config_input[CONF_HOST] == "10.11.12.13:4444"
            assert cf.config_input[CONF_APP_ID] == "ha_prod"
            assert cf.config_input[CONF_CREATE_SENSORS] == True
            assert cf.config_input[CONF_ALLERGEN_DEFENDER_SWITCH] == True
            assert cf.config_input[CONF_CREATE_INVERTER_POWER] == True
            assert cf.config_input[CONF_CREATE_DIAGNOSTICS_SENSORS] == True
            assert cf.config_input[CONF_CREATE_PARAMETERS] == True
            assert cf.config_input[CONF_PROTOCOL] == "https"

            assert try_to_connect.call_count == 1
            assert async_set_unique_id.call_count == 1
            assert async_set_unique_id.call_args[0][0] == "lennoxs30_10.11.12.13:4444"
            res["type"] == "form"
            res["step_id"] == "advanced"
            res["data_schema"] == cf.get_advanced_schema(False)
            len(res["errors"]) == 0

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(cf, "async_set_unique_id") as async_set_unique_id:
            with patch.object(cf, "try_to_connect") as try_to_connect:
                try_to_connect.side_effect = S30Exception("This is the error", EC_LOGIN, 100)
                user_input: dict = {}
                user_input[CONF_HOST] = "10.11.12.13:4444"
                user_input[CONF_APP_ID] = "ha_prod"
                user_input[CONF_CREATE_SENSORS] = True
                user_input[CONF_ALLERGEN_DEFENDER_SWITCH] = True
                user_input[CONF_CREATE_INVERTER_POWER] = True
                user_input[CONF_CREATE_DIAGNOSTICS_SENSORS] = True
                user_input[CONF_CREATE_PARAMETERS] = True
                user_input[CONF_PROTOCOL] = "https"
                cf.config_input = {}
                cf.config_input[CONF_CLOUD_CONNECTION] = False
                res = await cf.async_step_local(user_input=user_input)
                assert len(cf.config_input) == 1
                res["type"] == "form"
                res["step_id"] == "local"
                res["data_schema"] == STEP_LOCAL
                len(res["errors"]) == 1
                res["errors"]["base"] = "unable_to_connect_local"
                assert len(caplog.messages) == 1
                assert "This is the error" in caplog.messages[0]

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(cf, "_host_in_configuration_exists") as _host_in_configuration_exists:
            _host_in_configuration_exists.return_value = True
            user_input: dict = {}
            user_input[CONF_HOST] = "10.11.12.13:4444"
            user_input[CONF_APP_ID] = "ha_prod"
            user_input[CONF_CREATE_SENSORS] = True
            user_input[CONF_ALLERGEN_DEFENDER_SWITCH] = True
            user_input[CONF_CREATE_INVERTER_POWER] = True
            user_input[CONF_CREATE_DIAGNOSTICS_SENSORS] = True
            user_input[CONF_CREATE_PARAMETERS] = True
            user_input[CONF_PROTOCOL] = "https"
            cf.config_input = {}
            cf.config_input[CONF_CLOUD_CONNECTION] = False
            res = await cf.async_step_local(user_input=user_input)
            assert len(cf.config_input) == 1
            res["type"] == "form"
            res["step_id"] == "local"
            res["data_schema"] == STEP_LOCAL
            len(res["errors"]) == 1
            res["errors"][CONF_HOST] = "already_configured"

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        user_input: dict = {}
        user_input[CONF_HOST] = "<>!!!!@@"
        user_input[CONF_APP_ID] = "ha_prod"
        user_input[CONF_CREATE_SENSORS] = True
        user_input[CONF_ALLERGEN_DEFENDER_SWITCH] = True
        user_input[CONF_CREATE_INVERTER_POWER] = True
        user_input[CONF_CREATE_DIAGNOSTICS_SENSORS] = True
        user_input[CONF_CREATE_PARAMETERS] = True
        user_input[CONF_PROTOCOL] = "https"
        cf.config_input = {}
        cf.config_input[CONF_CLOUD_CONNECTION] = False
        res = await cf.async_step_local(user_input=user_input)
        assert len(cf.config_input) == 1
        res["type"] == "form"
        res["step_id"] == "local"
        res["data_schema"] == STEP_LOCAL
        len(res["errors"]) == 1
        res["errors"][CONF_HOST] = "invalid_hostname"


@pytest.mark.asyncio
async def test_lennoxS30ConfigFlow_async_step_advanced(manager: Manager, hass, caplog):
    cf = lennoxs30ConfigFlow()
    cf.hass = hass

    with patch.object(cf, "create_entry") as create_entry:
        create_entry.return_value = "yyyy"
        user_input = {}
        user_input["something"] = "x"
        cf.config_input = {}
        cf.config_input[CONF_CLOUD_CONNECTION] = False
        res = await cf.async_step_advanced(user_input=user_input)
        assert res == "yyyy"
        assert len(cf.config_input) == 2
        assert cf.config_input["something"] == "x"


@pytest.mark.asyncio
async def test_lennoxS30ConfigFlow_async_get_options_flow(manager: Manager, hass, caplog):
    cf = lennoxs30ConfigFlow().async_get_options_flow(manager.config_entry)
    cf.hass = hass
    assert isinstance(cf, OptionsFlowHandler)


@pytest.mark.asyncio
async def test_OptionsFlowHandler_async_step_init_local(config_entry_local, hass, caplog):
    cf = OptionsFlowHandler(config_entry_local)
    res = await cf.async_step_init(user_input=None)
    assert res["step_id"] == "init"

    # TODO validate each scheme element
    schema = res["data_schema"].schema

    si = schema[CONF_APP_ID]
    si = schema[CONF_CREATE_SENSORS]
    si = schema[CONF_ALLERGEN_DEFENDER_SWITCH]
    si = schema[CONF_CREATE_INVERTER_POWER]
    si = schema[CONF_CREATE_DIAGNOSTICS_SENSORS]
    si = schema[CONF_CREATE_PARAMETERS]
    si = schema[CONF_SCAN_INTERVAL]
    si = schema[CONF_INIT_WAIT_TIME]
    si = schema[CONF_FAST_POLL_INTERVAL]
    si = schema[CONF_FAST_POLL_COUNT]
    si = schema[CONF_TIMEOUT]
    si = schema[CONF_PROTOCOL]
    si = schema[CONF_PII_IN_MESSAGE_LOGS]
    si = schema[CONF_MESSAGE_DEBUG_LOGGING]
    si = schema[CONF_LOG_MESSAGES_TO_FILE]
    si = schema[CONF_MESSAGE_DEBUG_FILE]
    assert len(schema) == 16


@pytest.mark.asyncio
async def test_OptionsFlowHandler_async_step_init_cloud(config_entry_cloud, hass, caplog):
    cf = OptionsFlowHandler(config_entry_cloud)
    res = await cf.async_step_init(user_input=None)
    assert res["step_id"] == "init"

    # TODO validate each scheme element
    schema = res["data_schema"].schema
    si = schema[CONF_PASSWORD]
    si = schema[CONF_APP_ID]
    si = schema[CONF_CREATE_SENSORS]
    si = schema[CONF_ALLERGEN_DEFENDER_SWITCH]
    si = schema[CONF_SCAN_INTERVAL]
    si = schema[CONF_INIT_WAIT_TIME]
    si = schema[CONF_FAST_POLL_INTERVAL]
    si = schema[CONF_FAST_POLL_COUNT]
    si = schema[CONF_TIMEOUT]
    si = schema[CONF_PII_IN_MESSAGE_LOGS]
    si = schema[CONF_MESSAGE_DEBUG_LOGGING]
    si = schema[CONF_LOG_MESSAGES_TO_FILE]
    si = schema[CONF_MESSAGE_DEBUG_FILE]

    assert len(schema) == 13


@pytest.mark.asyncio
async def test_OptionsFlowHandler_async_step_init_cloud_save(
    config_entry_cloud: config_entries.ConfigEntry, hass, caplog
):
    cf = OptionsFlowHandler(config_entry_cloud)
    cf.hass = hass
    user_input = {}
    user_input[CONF_LOG_MESSAGES_TO_FILE] = False
    user_input[CONF_MESSAGE_DEBUG_FILE] = "s30_message.log"

    with patch.object(hass.config_entries, "async_update_entry") as async_update_entry:
        res = await cf.async_step_init(user_input=user_input)

        assert async_update_entry.call_count == 1
        call = async_update_entry.mock_calls[0]
        data = call.kwargs["data"]

        assert data[CONF_EMAIL] == config_entry_cloud.data[CONF_EMAIL]
        assert data[CONF_CLOUD_CONNECTION] == config_entry_cloud.data[CONF_CLOUD_CONNECTION]
        assert data[CONF_LOG_MESSAGES_TO_FILE] == False
        assert data[CONF_MESSAGE_DEBUG_FILE] == ""

        assert res["type"] == "create_entry"


@pytest.mark.asyncio
async def test_OptionsFlowHandler_async_step_init_local_save(
    config_entry_local: config_entries.ConfigEntry, hass, caplog
):
    cf = OptionsFlowHandler(config_entry_local)
    cf.hass = hass
    user_input = {}
    user_input[CONF_LOG_MESSAGES_TO_FILE] = True
    user_input[CONF_MESSAGE_DEBUG_FILE] = "s30_message.log"

    with patch.object(hass.config_entries, "async_update_entry") as async_update_entry:
        res = await cf.async_step_init(user_input=user_input)

        assert async_update_entry.call_count == 1
        call = async_update_entry.mock_calls[0]
        data = call.kwargs["data"]

        assert data[CONF_HOST] == config_entry_local.data[CONF_HOST]
        assert data[CONF_LOG_MESSAGES_TO_FILE] == True
        assert data[CONF_MESSAGE_DEBUG_FILE] == "s30_message.log"

        assert res["type"] == "create_entry"


@pytest.mark.asyncio
async def test_lennoxS30ConfigFlow_try_to_connect_cloud(manager: Manager, hass, caplog):
    cf = lennoxs30ConfigFlow()
    cf.config_input = {}
    cf.config_input[CONF_CLOUD_CONNECTION] = True
    cf.hass = hass

    with patch.object(Manager, "connect") as connect:
        with patch.object(Manager, "async_shutdown") as async_shutdown:
            user_input: dict = {}
            user_input[CONF_EMAIL] = "pete.rage@rage.com"
            user_input[CONF_PASSWORD] = "secret"
            user_input[CONF_APP_ID] = "ha_prod"
            await cf.try_to_connect(user_input)
            assert connect.call_count == 1
            assert async_shutdown.call_count == 1

            assert cf.manager.api._username == user_input[CONF_EMAIL]
            assert cf.manager.api._password == user_input[CONF_PASSWORD]
            assert cf.manager.api._applicationid == user_input[CONF_APP_ID]
            assert cf.manager.api.isLANConnection == False


@pytest.mark.asyncio
async def test_lennoxS30ConfigFlow_try_to_connect_local(manager: Manager, hass, caplog):
    cf = lennoxs30ConfigFlow()
    cf.config_input = {}
    cf.config_input[CONF_CLOUD_CONNECTION] = False
    cf.hass = hass

    with patch.object(Manager, "connect") as connect:
        with patch.object(Manager, "async_shutdown") as async_shutdown:
            user_input: dict = {}
            user_input[CONF_HOST] = "192.168.1.1:433"
            user_input[CONF_APP_ID] = "ha_prod"
            user_input[CONF_PROTOCOL] = "https"
            await cf.try_to_connect(user_input)
            assert connect.call_count == 1
            assert async_shutdown.call_count == 1

            assert cf.manager.api._applicationid == user_input[CONF_APP_ID]
            assert cf.manager.api.isLANConnection == True
            assert cf.manager.api.ip == user_input[CONF_HOST]
            assert cf.manager.api._protocol == user_input[CONF_PROTOCOL]
