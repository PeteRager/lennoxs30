"""template conftest."""
import json
import os

import pytest

from homeassistant import loader
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import (
    assert_setup_component,
    async_mock_service,
)

from homeassistant import config_entries

from custom_components.lennoxs30 import (
    DOMAIN,
    Manager,
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


def loadfile(name) -> json:
    script_dir = os.path.dirname(__file__) + "/messages/"
    file_path = os.path.join(script_dir, name)
    with open(file_path) as f:
        data = json.load(f)
    return data


@pytest.fixture
def manager(hass) -> Manager:

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
    )
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
