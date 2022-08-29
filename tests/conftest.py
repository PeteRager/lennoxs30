"""template conftest."""
import json
import os

import pytest

from homeassistant import loader
from homeassistant.setup import async_setup_component
from lennoxs30api.lennox_equipment import (
    lennox_equipment_parameter,
    lennox_equipment,
)

from pytest_homeassistant_custom_component.common import (
    assert_setup_component,
    async_mock_service,
)

from homeassistant import config_entries

from custom_components.lennoxs30 import (
    DOMAIN,
    Manager,
)

from homeassistant.const import (
    CONF_HOST,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
)


from custom_components.lennoxs30.const import (
    CONF_ALLERGEN_DEFENDER_SWITCH,
    CONF_APP_ID,
    CONF_CLOUD_CONNECTION,
    CONF_CREATE_INVERTER_POWER,
    CONF_CREATE_DIAGNOSTICS_SENSORS,
    CONF_CREATE_SENSORS,
    CONF_FAST_POLL_INTERVAL,
    CONF_FAST_POLL_COUNT,
    CONF_INIT_WAIT_TIME,
    CONF_LOG_MESSAGES_TO_FILE,
    CONF_MESSAGE_DEBUG_FILE,
    CONF_MESSAGE_DEBUG_LOGGING,
    CONF_PII_IN_MESSAGE_LOGS,
    DEFAULT_CLOUD_TIMEOUT,
    DEFAULT_LOCAL_TIMEOUT,
    LENNOX_DEFAULT_CLOUD_APP_ID,
    LENNOX_DEFAULT_LOCAL_APP_ID,
    CONF_LOCAL_CONNECTION,
    CONF_CREATE_PARAMETERS,
)

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def calls(hass):
    """Track calls to a mock service."""
    return async_mock_service(hass, "test", "automation")


@pytest.fixture
async def start_ha(hass, domains, caplog):
    """Do setup of integration."""
    for domain, value in domains.items():
        with assert_setup_component(value["count"], domain):
            assert await async_setup_component(
                hass,
                domain,
                value["config"],
            )
            await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()


@pytest.fixture
async def caplog_setup_text(caplog):
    """Return setup log of integration."""
    yield caplog.text


def loadfile(name: str, sysId: str = None) -> json:
    script_dir = os.path.dirname(__file__) + "/messages/"
    file_path = os.path.join(script_dir, name)
    with open(file_path) as f:
        data = json.load(f)
    if sysId != None:
        data["SenderID"] = sysId
    return data


@pytest.fixture
def config_entry_local() -> config_entries.ConfigEntry:
    config = config_entries.ConfigEntry(
        version=1, domain=DOMAIN, title="10.0.0.1", data={}, source="User"
    )
    config.unique_id = "12345"
    config.data = {}
    config.data[CONF_CLOUD_CONNECTION] = False
    config.data[CONF_HOST] = "10.0.0.1"
    config.data[CONF_APP_ID] = "ha_prod"
    config.data[CONF_CREATE_SENSORS] = True
    config.data[CONF_ALLERGEN_DEFENDER_SWITCH] = True
    config.data[CONF_CREATE_INVERTER_POWER] = True
    config.data[CONF_CREATE_DIAGNOSTICS_SENSORS] = True
    config.data[CONF_CREATE_PARAMETERS] = True
    config.data[CONF_SCAN_INTERVAL] = 10
    config.data[CONF_INIT_WAIT_TIME] = 30
    config.data[CONF_FAST_POLL_INTERVAL] = 1.0
    config.data[CONF_FAST_POLL_COUNT] = 5
    config.data[CONF_TIMEOUT] = 30
    config.data[CONF_PROTOCOL] = "https"
    config.data[CONF_FAST_POLL_COUNT] = 5
    config.data[CONF_PII_IN_MESSAGE_LOGS] = False
    config.data[CONF_MESSAGE_DEBUG_LOGGING] = False
    config.data[CONF_LOG_MESSAGES_TO_FILE] = False
    config.data[CONF_MESSAGE_DEBUG_FILE] = ""
    return config


@pytest.fixture
def config_entry_cloud() -> config_entries.ConfigEntry:
    config = config_entries.ConfigEntry(
        version=1, domain=DOMAIN, title="10.0.0.1", data={}, source="User"
    )
    config.unique_id = "12345"
    config.data = {}
    config.data[CONF_CLOUD_CONNECTION] = True
    config.data[CONF_EMAIL] = "pete.rage@rage.com"
    config.data[CONF_PASSWORD] = "secret"
    config.data[CONF_APP_ID] = "ha_prod"
    config.data[CONF_CREATE_SENSORS] = True
    config.data[CONF_ALLERGEN_DEFENDER_SWITCH] = True
    config.data[CONF_SCAN_INTERVAL] = 10
    config.data[CONF_INIT_WAIT_TIME] = 30
    config.data[CONF_FAST_POLL_INTERVAL] = 1.0
    config.data[CONF_FAST_POLL_COUNT] = 5
    config.data[CONF_TIMEOUT] = 30
    config.data[CONF_FAST_POLL_COUNT] = 5
    config.data[CONF_PII_IN_MESSAGE_LOGS] = False
    config.data[CONF_MESSAGE_DEBUG_LOGGING] = False
    config.data[CONF_LOG_MESSAGES_TO_FILE] = False
    config.data[CONF_MESSAGE_DEBUG_FILE] = ""
    return config


@pytest.fixture
def manager(hass, config_entry_local) -> Manager:
    config = config_entry_local

    manager = Manager(
        hass=hass,
        config=config,
        email=None,
        password=None,
        poll_interval=1,
        fast_poll_interval=2,
        allergenDefenderSwitch=False,
        app_id="HA",
        conf_init_wait_time=30,
        ip_address="10.0.0.1",
        create_sensors=False,
        create_inverter_power=False,
        protocol="https",
        index=0,
        pii_message_logs=False,
        message_debug_logging=True,
        message_logging_file=None,
        timeout=30,
        fast_poll_count=10,
    )
    manager.connected = True
    api = manager._api
    data = loadfile("login_response.json")
    api.process_login_response(data)

    data = loadfile("config_response_system_02.json")
    api.processMessage(data)

    data = loadfile("equipments_lcc_singlesetpoint.json")
    data["SenderID"] = "0000000-0000-0000-0000-000000000002"
    api.processMessage(data)

    data = loadfile("device_response_lcc.json")
    data["SenderID"] = "0000000-0000-0000-0000-000000000002"
    api.processMessage(data)

    return manager


@pytest.fixture
def manager_2_systems(hass) -> Manager:

    config = config_entries.ConfigEntry(
        version=1, domain=DOMAIN, title="10.0.0.1", data={}, source="User"
    )
    config.unique_id = "12345"

    manager = Manager(
        hass=hass,
        config=config,
        email=None,
        password=None,
        poll_interval=1,
        fast_poll_interval=2,
        allergenDefenderSwitch=False,
        app_id="HA",
        conf_init_wait_time=30,
        ip_address="10.0.0.1",
        create_sensors=False,
        create_inverter_power=False,
        protocol="https",
        index=0,
        pii_message_logs=False,
        message_debug_logging=True,
        message_logging_file=None,
        timeout=30,
        fast_poll_count=10,
    )
    manager.connected = True
    api = manager._api
    data = loadfile("login_response_2_systems.json")
    api.process_login_response(data)

    data = loadfile("config_response_system_02.json")
    api.processMessage(data)

    data = loadfile("equipments_lcc_singlesetpoint.json")
    data["SenderID"] = "0000000-0000-0000-0000-000000000002"
    api.processMessage(data)

    data = loadfile("device_response_lcc.json")
    data["SenderID"] = "0000000-0000-0000-0000-000000000002"
    api.processMessage(data)

    data = loadfile("config_response_system_01.json")
    api.processMessage(data)

    data = loadfile("equipments_lcc_singlesetpoint.json")
    data["SenderID"] = "0000000-0000-0000-0000-000000000001"
    api.processMessage(data)

    data = loadfile("device_response_lcc.json")
    data["SenderID"] = "0000000-0000-0000-0000-000000000001"
    api.processMessage(data)

    return manager


@pytest.fixture
def manager_mz(hass) -> Manager:

    config = config_entries.ConfigEntry(
        version=1, domain=DOMAIN, title="10.0.0.1", data={}, source="User"
    )
    config.unique_id = "12345"

    manager = Manager(
        hass=hass,
        config=config,
        email=None,
        password=None,
        poll_interval=1,
        fast_poll_interval=2,
        allergenDefenderSwitch=False,
        app_id="HA",
        conf_init_wait_time=30,
        ip_address="10.0.0.1",
        create_sensors=False,
        create_inverter_power=False,
        protocol="https",
        index=0,
        pii_message_logs=False,
        message_debug_logging=True,
        message_logging_file=None,
        timeout=30,
        fast_poll_count=10,
    )
    manager.connected = True
    api = manager._api
    data = loadfile("login_response_mz.json")
    api.process_login_response(data)

    data = loadfile("config_response_system_01.json")
    api.processMessage(data)

    data = loadfile("equipments_lcc_singlesetpoint.json")
    data["SenderID"] = "0000000-0000-0000-0000-000000000001"
    api.processMessage(data)

    data = loadfile("device_response_lcc.json")
    data["SenderID"] = "0000000-0000-0000-0000-000000000001"
    api.processMessage(data)

    return manager


@pytest.fixture
def manager_system_04_furn_ac_zoning(hass) -> Manager:

    config = config_entries.ConfigEntry(
        version=1, domain=DOMAIN, title="10.0.0.1", data={}, source="User"
    )
    config.unique_id = "12345"

    manager = Manager(
        hass=hass,
        config=config,
        email=None,
        password=None,
        poll_interval=1,
        fast_poll_interval=2,
        allergenDefenderSwitch=False,
        app_id="HA",
        conf_init_wait_time=30,
        ip_address="10.0.0.1",
        create_sensors=False,
        create_inverter_power=False,
        protocol="https",
        index=0,
        pii_message_logs=False,
        message_debug_logging=True,
        message_logging_file=None,
        timeout=30,
        fast_poll_count=10,
    )
    manager.connected = True
    api = manager._api
    data = loadfile("login_response_mz.json")
    api.process_login_response(data)

    data = loadfile(
        "system_04_furn_ac_zoning_config.json", "0000000-0000-0000-0000-000000000001"
    )
    api.processMessage(data)

    data = loadfile(
        "system_04_furn_ac_zoning_zones.json", "0000000-0000-0000-0000-000000000001"
    )
    api.processMessage(data)

    data = loadfile(
        "system_04_furn_ac_zoning_equipment.json",
        "0000000-0000-0000-0000-000000000001",
    )
    api.processMessage(data)

    data = loadfile("device_response_lcc.json", "0000000-0000-0000-0000-000000000001")
    api.processMessage(data)

    return manager


def conftest_parameter_extra_attributes(
    extra_state_attributes: dict,
    equipment: lennox_equipment,
    parameter: lennox_equipment_parameter,
):
    assert len(extra_state_attributes) == 3
    assert extra_state_attributes["equipment_id"] == equipment.equipment_id
    assert extra_state_attributes["equipment_type_id"] == equipment.equipType
    assert extra_state_attributes["parameter_id"] == parameter.pid
