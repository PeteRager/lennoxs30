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
    CONF_SENSORS,
)

import pytest

from homeassistant import config_entries, data_entry_flow
from custom_components.lennoxs30.const import (
    CONF_ALLERGEN_DEFENDER_SWITCH,
    CONF_CREATE_INVERTER_POWER,
    CONF_CREATE_SENSORS,
    CONF_FAST_POLL_INTERVAL,
    CONF_MESSAGE_DEBUG_FILE,
    CONF_MESSAGE_DEBUG_LOGGING,
    CONF_PII_IN_MESSAGE_LOGS,
)


from tests.common import MockConfigEntry

from custom_components.lennoxs30 import (
    DEFAULT_LOCAL_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    async_setup,
    create_migration_task,
)
from homeassistant.components import sensor
from homeassistant.helpers import entity_registry, entity_component

#
# @pytest.fixture(autouse=True)
# def zero_aggregation_time():
#    """Prevent the aggregation time from delaying the tests."""
#    with patch.object(config_flow, "DISCOVERY_AGGREGATION_TIME", 0):
#        yield


# @pytest.fixture(autouse=True)
# def mock_setup_entry():
#    """Mock setting up a config entry."""
#    with patch(
#        "homeassistant.components.apple_tv.async_setup_entry", return_value=True
#    ):
#        yield


# User Flows


@pytest.mark.asyncio
async def test_migrate_local_config(hass, caplog):
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
async def test_migrate_cloud_config(hass, caplog):
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
            assert migration_data[CONF_EMAIL] == "myemail@email.com"
            assert migration_data[CONF_PASSWORD] == "mypassword"
            assert migration_data[CONF_FAST_POLL_INTERVAL] == 0.75
            assert migration_data[CONF_CREATE_SENSORS] == False
            assert migration_data[CONF_ALLERGEN_DEFENDER_SWITCH] == False
            assert migration_data[CONF_CREATE_INVERTER_POWER] == False
            assert migration_data[CONF_PROTOCOL] == "https"
            assert migration_data[CONF_PII_IN_MESSAGE_LOGS] == False
            assert migration_data[CONF_MESSAGE_DEBUG_FILE] == ""
            assert migration_data[CONF_MESSAGE_DEBUG_LOGGING] == True
