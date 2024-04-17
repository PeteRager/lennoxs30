"""template conftest."""
# pylint: disable=logging-not-lazy
# pylint: disable=logging-fstring-interpolation
# pylint: disable=global-statement
# pylint: disable=broad-except
# pylint: disable=unused-argument
# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
import json
import logging
import os
from unittest.mock import patch

import pytest
import pytest_socket

from lennoxs30api.s30api_async import (
    lennox_system,
)
from lennoxs30api.lennox_equipment import (
    lennox_equipment_parameter,
    lennox_equipment,
)
from lennoxs30api.s30exception import S30Exception

from homeassistant.helpers import device_registry as dr
from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.number import NumberEntity
from homeassistant.components.select import SelectEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.setup import async_setup_component
from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
)
from homeassistant.core import HomeAssistant
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM, METRIC_SYSTEM

from pytest_homeassistant_custom_component.common import (
    assert_setup_component,
    async_mock_service,
)


from custom_components.lennoxs30 import (
    DOMAIN,
    DS_CONNECTED,
    DS_RETRY_WAIT,
    Manager,
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
    CONF_CREATE_PARAMETERS,
)

pytest_plugins = "pytest_homeassistant_custom_component"

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def disable_device_registry(hass):
    device_registry = dr.async_get(hass)
    with patch.object(device_registry, "async_get_or_create"):
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
    if sysId is not None:
        data["SenderID"] = sysId
    return data


@pytest.fixture
def config_entry_local() -> config_entries.ConfigEntry:
    config = config_entries.ConfigEntry(version=1, minor_version=0, domain=DOMAIN, title="10.0.0.1", data={}, source="User", unique_id="12345")
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
    config = config_entries.ConfigEntry(version=1, minor_version = 0, domain=DOMAIN, title="10.0.0.1", data={}, source="User", unique_id="12345")
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
def manager(hass: HomeAssistant, config_entry_local) -> Manager:
    config = config_entry_local
    hass.config.units = METRIC_SYSTEM
    manager_to_return = Manager(
        hass=hass,
        config=config,
        email=None,
        password=None,
        poll_interval=1,
        fast_poll_interval=2,
        allergen_defender_switch=False,
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
    manager_to_return.connected = True
    api = manager_to_return.api
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

    return manager_to_return


@pytest.fixture
def manager_us_customary_units(hass: HomeAssistant, config_entry_local) -> Manager:
    config = config_entry_local
    hass.config.units = US_CUSTOMARY_SYSTEM
    manager_to_return = Manager(
        hass=hass,
        config=config,
        email=None,
        password=None,
        poll_interval=1,
        fast_poll_interval=0.5,
        allergen_defender_switch=False,
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
    manager_to_return.connected = True
    api = manager_to_return.api
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

    return manager_to_return


@pytest.fixture
def manager_2_systems(hass) -> Manager:
    config = config_entries.ConfigEntry(version=1, minor_version = 0, domain=DOMAIN, title="10.0.0.1", data={}, source="User", unique_id="12345")

    manager_to_return = Manager(
        hass=hass,
        config=config,
        email=None,
        password=None,
        poll_interval=1,
        fast_poll_interval=2,
        allergen_defender_switch=False,
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
    manager_to_return.connected = True
    api = manager_to_return.api
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

    return manager_to_return


@pytest.fixture
def manager_mz(hass) -> Manager:
    config = config_entries.ConfigEntry(version=1, minor_version = 0, domain=DOMAIN, title="10.0.0.1", data={}, source="User", unique_id="12345")
    manager_to_return = Manager(
        hass=hass,
        config=config,
        email=None,
        password=None,
        poll_interval=1,
        fast_poll_interval=2,
        allergen_defender_switch=False,
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
    manager_to_return.connected = True
    api = manager_to_return.api
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

    return manager_to_return


@pytest.fixture
def manager_system_04_furn_ac_zoning(hass) -> Manager:
    config = config_entries.ConfigEntry(version=1, minor_version = 0, domain=DOMAIN, title="10.0.0.1", data={}, source="User", unique_id="12345")
    manager_to_return = Manager(
        hass=hass,
        config=config,
        email=None,
        password=None,
        poll_interval=1,
        fast_poll_interval=2,
        allergen_defender_switch=False,
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
    manager_to_return.connected = True
    api = manager_to_return.api
    data = loadfile("login_response_mz.json")
    api.process_login_response(data)

    data = loadfile("system_04_furn_ac_zoning_config.json", "0000000-0000-0000-0000-000000000001")
    api.processMessage(data)

    data = loadfile("system_04_furn_ac_zoning_zones.json", "0000000-0000-0000-0000-000000000001")
    api.processMessage(data)

    data = loadfile(
        "system_04_furn_ac_zoning_equipment.json",
        "0000000-0000-0000-0000-000000000001",
    )
    api.processMessage(data)

    data = loadfile("device_response_lcc.json", "0000000-0000-0000-0000-000000000001")
    api.processMessage(data)

    data = loadfile("system_04_furn_ac_zoning_indoorAirQuality.json", "0000000-0000-0000-0000-000000000001")
    api.processMessage(data)

    return manager_to_return


@pytest.fixture
def manager_system_04_furn_ac_zoning_ble(manager_system_04_furn_ac_zoning: Manager) -> Manager:
    api = manager_system_04_furn_ac_zoning.api
    data = loadfile("system_04_furn_ac_zoning_ble.json", "0000000-0000-0000-0000-000000000001")
    api.processMessage(data)

    return manager_system_04_furn_ac_zoning


def conftest_parameter_extra_attributes(
    extra_state_attributes: dict,
    equipment: lennox_equipment,
    parameter: lennox_equipment_parameter,
):
    assert len(extra_state_attributes) == 3
    assert extra_state_attributes["equipment_id"] == equipment.equipment_id
    assert extra_state_attributes["equipment_type_id"] == equipment.equipType
    assert extra_state_attributes["parameter_id"] == parameter.pid


def conftest_base_entity_availability(manager: Manager, system: lennox_system, c):
    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_RETRY_WAIT)
        assert update_callback.call_count == 1
        assert c.available is False

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_CONNECTED)
        assert update_callback.call_count == 1
        assert c.available is True
        system.attr_updater({"status": "online"}, "status", "cloud_status")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 2
        assert c.available is True
        system.attr_updater({"status": "offline"}, "status", "cloud_status")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 3
        assert c.available is False


async def conf_test_exception_handling(target, method_name: str, entity, async_method, **kwargs):
    with patch.object(target, method_name) as set_parameter_value:
        set_parameter_value.side_effect = S30Exception("This is the error", 100, 200)
        ex: HomeAssistantError = None
        try:
            await async_method(**kwargs)
        except HomeAssistantError as h_e:
            ex = h_e
        assert "This is the error" in str(ex)
        assert entity.name in str(ex)

    with patch.object(target, method_name) as set_parameter_value:
        set_parameter_value.side_effect = Exception("This is the error")
        ex: HomeAssistantError = None
        try:
            await async_method(**kwargs)
        except HomeAssistantError as h_e:
            ex = h_e
        assert "This is the error" in ex.args[0]
        assert "unexpected" in ex.args[0]
        assert entity.name in ex.args[0]


async def conf_test_number_info_async_set_native_value(target, method_name: str, entity: NumberEntity, caplog):
    with patch.object(target, method_name) as _:
        with caplog.at_level(logging.INFO):
            caplog.clear()
            try:
                await entity.async_set_native_value(100)
            except HomeAssistantError as _:
                pass
            assert len(caplog.messages) > 0
            assert caplog.records[0].levelname == "INFO"
            msg = caplog.records[0].message
            assert "value [100.0]" in msg
            assert f"name [{entity._myname}]" in msg
            assert f"{entity.__class__.__name__}::async_set_native_value" in msg


async def conf_test_select_info_async_select_option(target, method_name: str, entity: SelectEntity, caplog):
    with patch.object(target, method_name) as _:
        with caplog.at_level(logging.INFO):
            caplog.clear()
            try:
                await entity.async_select_option("Hello")
            except HomeAssistantError as _:
                pass
            assert len(caplog.messages) > 0
            assert caplog.records[0].levelname == "INFO"
            msg = caplog.records[0].message
            assert "option [Hello]" in msg
            assert f"name [{entity._myname}]" in msg
            assert f"{entity.__class__.__name__}::async_select_option" in msg


async def conf_test_switch_info_async_turn_on(target, method_name: str, entity: SwitchEntity, caplog):
    with patch.object(target, method_name) as _:
        with caplog.at_level(logging.INFO):
            caplog.clear()
            try:
                await entity.async_turn_on()
            except HomeAssistantError as _:
                pass
            assert len(caplog.messages) > 0
            assert caplog.records[0].levelname == "INFO"
            msg = caplog.records[0].message
            assert f"name [{entity._myname}]" in msg
            assert f"{entity.__class__.__name__}::async_turn_on" in msg


async def conf_test_switch_info_async_turn_off(target, method_name: str, entity: SwitchEntity, caplog):
    with patch.object(target, method_name) as _:
        with caplog.at_level(logging.INFO):
            caplog.clear()
            try:
                await entity.async_turn_off()
            except HomeAssistantError as _:
                pass
            assert len(caplog.messages) > 0
            assert caplog.records[0].levelname == "INFO"
            msg = caplog.records[0].message
            assert f"name [{entity._myname}]" in msg
            assert f"{entity.__class__.__name__}::async_turn_off" in msg


async def conf_test_button_info_async_press(target, method_name: str, entity: SwitchEntity, caplog):
    with patch.object(target, method_name) as _:
        with caplog.at_level(logging.INFO):
            caplog.clear()
            try:
                await entity.async_press()
            except HomeAssistantError as _:
                pass
            assert len(caplog.messages) > 0
            assert caplog.records[0].levelname == "INFO"
            msg = caplog.records[0].message
            assert f"name [{entity._myname}]" in msg
            assert f"{entity.__class__.__name__}::async_press" in msg
