import ipaddress
import re

import voluptuous as vol
from homeassistant.data_entry_flow import FlowResult
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import (
    CONF_NAME,
    CONF_EMAIL,
    CONF_HOSTS,
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.helpers import config_validation as cv
import logging

CONF_FAST_POLL_INTERVAL = "fast_scan_interval"
CONF_ALLERGEN_DEFENDER_SWITCH = "allergen_defender_switch"
CONF_APP_ID = "app_id"
CONF_INIT_WAIT_TIME = "init_wait_time"
CONF_CREATE_SENSORS = "create_sensors"
DEFAULT_POLL_INTERVAL: int = 10
DEFAULT_FAST_POLL_INTERVAL: float = 0.75
MAX_ERRORS = 5
RETRY_INTERVAL_SECONDS = 60
DOMAIN = "lennoxs30"
_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_NAME, default = "S30"): cv.string,
                vol.Required(CONF_EMAIL): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_HOSTS, default="Cloud"): str,
                vol.Optional(CONF_SCAN_INTERVAL): cv.positive_int,
                vol.Optional(
                    CONF_FAST_POLL_INTERVAL, default=DEFAULT_FAST_POLL_INTERVAL
                ): cv.positive_float,
                vol.Optional(CONF_ALLERGEN_DEFENDER_SWITCH, default=False): cv.boolean,
                vol.Optional(CONF_APP_ID): cv.string,
                vol.Optional(CONF_INIT_WAIT_TIME, default=30): cv.positive_int,
                vol.Optional(CONF_CREATE_SENSORS, default=False): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

def host_valid(host):
    """Return True if hostname or IP address is valid."""
    try:
        if ipaddress.ip_address(host).version == (4 or 6):
            return True
    except ValueError:
        disallowed = re.compile(r"[^a-zA-Z\d\-]")
        return all(x and not disallowed.search(x) for x in host.split("."))


@callback
def lennox30_entries(hass: HomeAssistant):
    """Return the hosts already configured."""
    return set(
        entry.data[CONF_HOST] for entry in hass.config_entries.async_entries(DOMAIN)
    )


class lennoxs30ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Lennox S30 configflow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def _host_in_configuration_exists(self, host) -> bool:
        """Return True if host exists in configuration."""
        if host in lennox30_entries(self.hass):
            return True
        return False

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOSTS]
            if host != "Cloud":
                if self._host_in_configuration_exists(host):
                    errors[CONF_HOSTS] = "already_configured"
                elif not host_valid(user_input[CONF_HOSTS]):
                    errors[CONF_HOSTS] = "invalid host IP"
                else:
                    await self.async_set_unique_id(user_input[CONF_HOSTS])
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=user_input[CONF_HOSTS], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_import(self, user_input) -> FlowResult:
        """Handle the import step."""
        await self.async_set_unique_id(user_input[CONF_HOSTS])
        self._abort_if_unique_id_configured()
        return await self.async_step_user(user_input)