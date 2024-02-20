"""Test config flow."""
# pylint: disable=global-statement
# pylint: disable=broad-except
# pylint: disable=unused-argument
# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=too-many-lines
# pylint: disable=fixme
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access


import logging
from unittest.mock import patch

import pytest

from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import (
    CONF_TIMEOUT,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from lennoxs30api.s30exception import S30Exception, EC_LOGIN, EC_COMMS_ERROR, EC_CONFIG_TIMEOUT


from custom_components.lennoxs30.const import (
    CONF_FAST_POLL_COUNT,
    LENNOX_DOMAIN,
    MANAGER,
)
from custom_components.lennoxs30 import (
    DOMAIN,
    DOMAIN_STATE,
    PLATFORMS,
    Manager,
    async_setup_entry,
    DS_LOGIN_FAILED,
    async_unload_entry,
)


@pytest.mark.asyncio
async def test_async_setup_entry_local(hass: HomeAssistant, caplog):
    data = {
        "cloud_connection": False,
        "host": "192.168.1.93",
        "app_id": "homeassistant",
        "create_sensors": True,
        "allergen_defender_switch": False,
        "create_inverter_power": False,
        "create_diagnostic_sensors": False,
        "create_parameters": False,
        "protocol": "https",
        "scan_interval": 1,
        "fast_scan_interval": 0.75,
        "init_wait_time": 30,
        "pii_in_message_logs": False,
        "message_debug_logging": True,
        "log_messages_to_file": False,
        "message_debug_file": "messages.log",
        CONF_FAST_POLL_COUNT: 5,
        CONF_TIMEOUT: 30,
    }
    hass.data[LENNOX_DOMAIN] = {}

    config_entry = config_entries.ConfigEntry(1, DOMAIN, "Test", data, "my_source")

    with patch("custom_components.lennoxs30.Manager.s30_initialize") as s30_initialize:
        res = await async_setup_entry(hass, config_entry)
        assert res is True
        manager: Manager = hass.data[LENNOX_DOMAIN][config_entry.unique_id][MANAGER]
        assert s30_initialize.call_count == 1

        assert manager.config_entry == config_entry
        assert manager._hass == hass
        assert manager._config == config_entry
        assert manager._poll_interval == 1
        assert manager._fast_poll_interval == 0.75
        assert manager._fast_poll_count == 5
        assert manager._protocol == "https"
        assert manager._ip_address == "192.168.1.93"
        assert manager._pii_message_log is False
        assert manager._message_debug_logging is True
        assert manager._message_logging_file == "messages.log"
        assert manager.allergen_defender_switch is False
        assert manager.create_sensors is True
        assert manager.create_alert_sensors is True
        assert manager.create_inverter_power is False
        assert manager.create_diagnostic_sensors is False
        assert manager.create_equipment_parameters is False
        assert manager._conf_init_wait_time == 30
        assert manager.is_metric is True
        assert manager.connection_state == DOMAIN_STATE

    with patch("custom_components.lennoxs30.Manager.s30_initialize") as s30_initialize:
        with patch("custom_components.lennoxs30.Manager.updateState") as update_state:
            s30_initialize.side_effect = S30Exception("login error", EC_LOGIN, 0)
            ex: HomeAssistantError = None
            try:
                res = await async_setup_entry(hass, config_entry)
            except HomeAssistantError as he:
                ex = he
            assert ex is not None
            assert "unable to login" in str(ex)
            assert "please check credential" in str(ex)
            assert update_state.call_count == 1
            assert update_state.call_args[0][0] == DS_LOGIN_FAILED

    with caplog.at_level(logging.INFO):
        caplog.clear()
        with patch("custom_components.lennoxs30.Manager.s30_initialize") as s30_initialize:
            with patch("custom_components.lennoxs30.Manager.updateState") as update_state:
                with patch("asyncio.create_task") as create_task:
                    s30_initialize.side_effect = S30Exception("Timeout waiting for config", EC_CONFIG_TIMEOUT, 0)
                    ex: HomeAssistantError = None
                    res = await async_setup_entry(hass, config_entry)
                    manager: Manager = hass.data[LENNOX_DOMAIN][config_entry.unique_id][MANAGER]

                    assert res is True

                    assert create_task.call_count == 1
                    assert create_task.call_args[0][0].__name__ == "initialize_retry_task"

                    assert len(caplog.messages) >= 2

                    record = caplog.records[len(caplog.messages) - 2]
                    assert record.levelname == "WARNING"
                    assert "Timeout waiting for config" in record.message

                    record = caplog.records[len(caplog.messages) - 1]
                    assert record.levelname == "INFO"
                    assert "connection will be retried" in record.message

    with caplog.at_level(logging.INFO):
        caplog.clear()
        with patch("custom_components.lennoxs30.Manager.s30_initialize") as s30_initialize:
            with patch("custom_components.lennoxs30.Manager.updateState") as update_state:
                with patch("asyncio.create_task") as create_task:
                    s30_initialize.side_effect = S30Exception("Transport Error", EC_COMMS_ERROR, 0)
                    ex: HomeAssistantError = None
                    res = await async_setup_entry(hass, config_entry)
                    manager: Manager = hass.data[LENNOX_DOMAIN][config_entry.unique_id][MANAGER]

                    assert res is True

                    assert create_task.call_count == 1
                    assert create_task.call_args[0][0].__name__ == "initialize_retry_task"

                    assert len(caplog.messages) >= 2

                    record = caplog.records[len(caplog.messages) - 2]
                    assert record.levelname == "ERROR"
                    assert "Transport Error" in record.message

                    record = caplog.records[len(caplog.messages) - 1]
                    assert record.levelname == "INFO"
                    assert "connection will be retried" in record.message


@pytest.mark.asyncio
async def test_async_setup_entry_cloud(hass, caplog):
    data = {
        "cloud_connection": True,
        "email": "pete.rage@rage.com",
        "password": "rage",
        "app_id": "homeassistant",
        "create_sensors": True,
        "allergen_defender_switch": False,
        "create_inverter_power": False,
        "create_diagnostic_sensors": False,
        "create_parameters": False,
        "scan_interval": 1,
        "fast_scan_interval": 0.75,
        "init_wait_time": 30,
        "pii_in_message_logs": False,
        "message_debug_logging": True,
        "log_messages_to_file": False,
        "message_debug_file": "",
        CONF_FAST_POLL_COUNT: 5,
        CONF_TIMEOUT: 30,
    }
    hass.data[LENNOX_DOMAIN] = {}

    config_entry = config_entries.ConfigEntry(1, DOMAIN, "Test", data, "my_source")

    with patch("custom_components.lennoxs30.Manager.s30_initialize") as s30_initialize:
        res = await async_setup_entry(hass, config_entry)
        assert res is True
        manager: Manager = hass.data[LENNOX_DOMAIN][config_entry.unique_id][MANAGER]
        assert s30_initialize.call_count == 1

        assert manager.config_entry == config_entry
        assert manager._hass == hass
        assert manager._config == config_entry
        assert manager._poll_interval == 1
        assert manager._fast_poll_interval == 0.75
        assert manager._fast_poll_count == 5
        assert manager.api._username == "pete.rage@rage.com"
        assert manager.api._password == "rage"
        assert manager._pii_message_log is False
        assert manager._message_debug_logging is True
        assert manager._message_logging_file is None
        assert manager.allergen_defender_switch is False
        assert manager.create_sensors is True
        assert manager.create_alert_sensors is True
        assert manager.create_inverter_power is False
        assert manager.create_diagnostic_sensors is False
        assert manager.create_equipment_parameters is False
        assert manager._conf_init_wait_time == 30
        assert manager.is_metric is True
        assert manager.connection_state == DOMAIN_STATE


@pytest.mark.asyncio
async def test_async_setup_entry_multiple(hass, caplog):
    data = {
        "cloud_connection": False,
        "host": "192.168.1.93",
        "app_id": "homeassistant",
        "create_sensors": True,
        "allergen_defender_switch": False,
        "create_inverter_power": False,
        "create_diagnostic_sensors": False,
        "create_parameters": False,
        "protocol": "https",
        "scan_interval": 1,
        "fast_scan_interval": 0.75,
        "init_wait_time": 30,
        "pii_in_message_logs": False,
        "message_debug_logging": True,
        "log_messages_to_file": False,
        "message_debug_file": "messages.log",
        CONF_FAST_POLL_COUNT: 5,
        CONF_TIMEOUT: 30,
    }
    hass.data[LENNOX_DOMAIN] = {}

    config_entry = config_entries.ConfigEntry(1, DOMAIN, "Test", data, "my_source")

    with patch("custom_components.lennoxs30.Manager.s30_initialize") as s30_initialize:
        res = await async_setup_entry(hass, config_entry)
        assert res is True
        manager: Manager = hass.data[LENNOX_DOMAIN][config_entry.unique_id][MANAGER]
        assert s30_initialize.call_count == 1

        assert manager.config_entry == config_entry
        assert manager._hass == hass
        assert manager._config == config_entry
        assert manager._poll_interval == 1
        assert manager._fast_poll_interval == 0.75
        assert manager._fast_poll_count == 5
        assert manager._protocol == "https"
        assert manager._ip_address == "192.168.1.93"
        assert manager._pii_message_log is False
        assert manager._message_debug_logging is True
        assert manager._message_logging_file == "messages.log"
        assert manager.allergen_defender_switch is False
        assert manager.create_sensors is True
        assert manager.create_alert_sensors is True
        assert manager.create_inverter_power is False
        assert manager.create_diagnostic_sensors is False
        assert manager.create_equipment_parameters is False
        assert manager._conf_init_wait_time == 30
        assert manager.is_metric is True
        assert manager.connection_state == DOMAIN_STATE

    data = {
        "cloud_connection": False,
        "host": "192.168.1.94",
        "create_sensors": True,
        "allergen_defender_switch": False,
        "create_inverter_power": False,
        "create_diagnostic_sensors": False,
        "create_parameters": False,
        "protocol": "https",
        "scan_interval": 1,
        "fast_scan_interval": 0.75,
        "init_wait_time": 30,
        "pii_in_message_logs": False,
        "message_debug_logging": True,
        "log_messages_to_file": False,
        "message_debug_file": "messages.log",
        CONF_FAST_POLL_COUNT: 5,
        CONF_TIMEOUT: 30,
    }
    hass.data[LENNOX_DOMAIN] = {}

    config_entry = config_entries.ConfigEntry(1, DOMAIN, "Test1", data, "my_source")

    with patch("custom_components.lennoxs30.Manager.s30_initialize") as s30_initialize:
        res = await async_setup_entry(hass, config_entry)
        assert res is True
        manager: Manager = hass.data[LENNOX_DOMAIN][config_entry.unique_id][MANAGER]
        assert s30_initialize.call_count == 1

        assert manager.config_entry == config_entry
        assert manager._hass == hass
        assert manager._config == config_entry
        assert manager._poll_interval == 1
        assert manager._fast_poll_interval == 0.75
        assert manager._fast_poll_count == 5
        assert manager._protocol == "https"
        assert manager._ip_address == "192.168.1.94"
        assert manager._pii_message_log is False
        assert manager._message_debug_logging is True
        assert manager._message_logging_file == "messages.log"
        assert manager.allergen_defender_switch is False
        assert manager.create_sensors is True
        assert manager.create_alert_sensors is True
        assert manager.create_inverter_power is False
        assert manager.create_diagnostic_sensors is False
        assert manager.create_equipment_parameters is False
        assert manager._conf_init_wait_time == 30
        assert manager.is_metric is True
        assert manager.connection_state == "lennoxs30.conn_192_168_1_94"

    data = {
        "cloud_connection": True,
        "email": "pete._rage@rage.com",
        "password": "rage",
        "app_id": "homeassistant",
        "create_sensors": True,
        "allergen_defender_switch": False,
        "create_inverter_power": False,
        "create_diagnostic_sensors": False,
        "create_parameters": False,
        "scan_interval": 1,
        "fast_scan_interval": 0.75,
        "init_wait_time": 30,
        "pii_in_message_logs": False,
        "message_debug_logging": True,
        "log_messages_to_file": False,
        "message_debug_file": "",
        CONF_FAST_POLL_COUNT: 5,
        CONF_TIMEOUT: 30,
    }
    hass.data[LENNOX_DOMAIN] = {}

    config_entry = config_entries.ConfigEntry(1, DOMAIN, "Test3", data, "my_source")

    with patch("custom_components.lennoxs30.Manager.s30_initialize") as s30_initialize:
        res = await async_setup_entry(hass, config_entry)
        assert res is True
        manager: Manager = hass.data[LENNOX_DOMAIN][config_entry.unique_id][MANAGER]
        assert s30_initialize.call_count == 1

        assert manager.config_entry == config_entry
        assert manager._hass == hass
        assert manager._config == config_entry
        assert manager._poll_interval == 1
        assert manager._fast_poll_interval == 0.75
        assert manager._fast_poll_count == 5
        assert manager.api._username == "pete._rage@rage.com"
        assert manager.api._password == "rage"
        assert manager._pii_message_log is False
        assert manager._message_debug_logging is True
        assert manager._message_logging_file is None
        assert manager.allergen_defender_switch is False
        assert manager.create_sensors is True
        assert manager.create_alert_sensors is True
        assert manager.create_inverter_power is False
        assert manager.create_diagnostic_sensors is False
        assert manager.create_equipment_parameters is False
        assert manager._conf_init_wait_time == 30
        assert manager.is_metric is True
        assert manager.connection_state == "lennoxs30.conn_pete_rage"


@pytest.mark.asyncio
async def test_async_unload_entry_success(hass, caplog):
    data = {
        "cloud_connection": False,
        "host": "192.168.1.93",
        "app_id": "homeassistant",
        "create_sensors": True,
        "allergen_defender_switch": False,
        "create_inverter_power": False,
        "create_diagnostic_sensors": False,
        "create_parameters": False,
        "protocol": "https",
        "scan_interval": 1,
        "fast_scan_interval": 0.75,
        "init_wait_time": 30,
        "pii_in_message_logs": False,
        "message_debug_logging": True,
        "log_messages_to_file": False,
        "message_debug_file": "messages.log",
        CONF_FAST_POLL_COUNT: 5,
        CONF_TIMEOUT: 30,
    }
    hass.data[LENNOX_DOMAIN] = {}

    config_entry = config_entries.ConfigEntry(1, DOMAIN, "Test", data, "my_source")

    with patch("custom_components.lennoxs30.Manager.s30_initialize") as _:
        res = await async_setup_entry(hass, config_entry)
        assert res is True
        manager: Manager = hass.data[LENNOX_DOMAIN][config_entry.unique_id][MANAGER]
        with patch.object(hass.config_entries, "async_unload_platforms") as mock_unload_platforms:
            with patch.object(manager, "async_shutdown") as mockasync_shutdown:
                mock_unload_platforms.return_value = True
                res = await async_unload_entry(hass, config_entry)
                assert mock_unload_platforms.call_count == 1
                assert mock_unload_platforms.call_args[0][0] == config_entry
                assert mock_unload_platforms.call_args[0][1] == PLATFORMS

                assert mockasync_shutdown.call_count == 1
                assert mockasync_shutdown.call_args[0][0] is None

                assert hass.data[LENNOX_DOMAIN].get(config_entry.unique_id) is None

                assert res is True


@pytest.mark.asyncio
async def test_async_unload_entry_unload_fail(hass, caplog):
    data = {
        "cloud_connection": False,
        "host": "192.168.1.93",
        "app_id": "homeassistant",
        "create_sensors": True,
        "allergen_defender_switch": False,
        "create_inverter_power": False,
        "create_diagnostic_sensors": False,
        "create_parameters": False,
        "protocol": "https",
        "scan_interval": 1,
        "fast_scan_interval": 0.75,
        "init_wait_time": 30,
        "pii_in_message_logs": False,
        "message_debug_logging": True,
        "log_messages_to_file": False,
        "message_debug_file": "messages.log",
        CONF_FAST_POLL_COUNT: 5,
        CONF_TIMEOUT: 30,
    }
    hass.data[LENNOX_DOMAIN] = {}

    config_entry = config_entries.ConfigEntry(1, DOMAIN, "Test", data, "my_source")

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch("custom_components.lennoxs30.Manager.s30_initialize") as _:
            res = await async_setup_entry(hass, config_entry)
            assert res is True
            manager: Manager = hass.data[LENNOX_DOMAIN][config_entry.unique_id][MANAGER]
            with patch.object(hass.config_entries, "async_unload_platforms") as mock_unload_platforms:
                mock_unload_platforms.return_value = False
                with patch.object(manager, "async_shutdown") as mockasync_shutdown:
                    res = await async_unload_entry(hass, config_entry)
                    assert mock_unload_platforms.call_count == 1
                    assert mock_unload_platforms.call_args[0][0] == config_entry
                    assert mock_unload_platforms.call_args[0][1] == PLATFORMS

                    assert mockasync_shutdown.call_count == 0
                    assert hass.data[LENNOX_DOMAIN].get(config_entry.unique_id) is not None

                    assert res is False

                    assert len(caplog.records) == 1
                    msg = caplog.messages[0]
                    assert "call to hass.config_entries.async_unload_platforms returned False" in msg

            with patch.object(hass.config_entries, "async_unload_platforms") as mock_unload_platforms:
                mock_unload_platforms.return_value = True
                with patch.object(manager, "async_shutdown") as mockasync_shutdown:
                    mockasync_shutdown.side_effect = S30Exception("This is the error", EC_COMMS_ERROR, 0)
                    caplog.clear()
                    res = await async_unload_entry(hass, config_entry)
                    assert mock_unload_platforms.call_count == 1
                    assert mock_unload_platforms.call_args[0][0] == config_entry
                    assert mock_unload_platforms.call_args[0][1] == PLATFORMS

                    assert mockasync_shutdown.call_count == 1
                    assert hass.data[LENNOX_DOMAIN].get(config_entry.unique_id) is None

                    assert res is True

                    assert len(caplog.records) == 1
                    msg = caplog.messages[0]
                    assert "async_unload_entry" in msg
                    assert "This is the error" in msg
                    assert str(config_entry.unique_id) in msg

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch("custom_components.lennoxs30.Manager.s30_initialize") as _:
            res = await async_setup_entry(hass, config_entry)
            assert res is True
            manager: Manager = hass.data[LENNOX_DOMAIN][config_entry.unique_id][MANAGER]
            with patch.object(hass.config_entries, "async_unload_platforms") as mock_unload_platforms:
                mock_unload_platforms.return_value = True
                with patch.object(manager, "async_shutdown") as mockasync_shutdown:
                    mockasync_shutdown.side_effect = ValueError("bad value")
                    caplog.clear()
                    res = await async_unload_entry(hass, config_entry)
                    assert mock_unload_platforms.call_count == 1
                    assert mock_unload_platforms.call_args[0][0] == config_entry
                    assert mock_unload_platforms.call_args[0][1] == PLATFORMS

                    assert mockasync_shutdown.call_count == 1
                    assert hass.data[LENNOX_DOMAIN].get(config_entry.unique_id) is None

                    assert res is True

                    assert len(caplog.records) == 1
                    msg = caplog.messages[0]
                    assert "async_unload_entry" in msg
                    assert "unexpected exception" in msg
                    assert str(config_entry.unique_id) in msg
