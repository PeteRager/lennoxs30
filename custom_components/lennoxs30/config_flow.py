import ipaddress
import re

import voluptuous as vol
from config.custom_components.lennoxs30.const import (
    CONF_ALLERGEN_DEFENDER_SWITCH,
    CONF_APP_ID,
    CONF_CLOUD_CONNECTION,
    CONF_CREATE_INVERTER_POWER,
    CONF_CREATE_SENSORS,
    CONF_FAST_POLL_INTERVAL,
    CONF_INIT_WAIT_TIME,
    CONF_LOG_MESSAGES_TO_FILE,
    CONF_MESSAGE_DEBUG_FILE,
    CONF_MESSAGE_DEBUG_LOGGING,
    CONF_PII_IN_MESSAGE_LOGS,
)
from homeassistant.data_entry_flow import FlowResult
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import (
    CONF_HOST,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
)
from homeassistant.helpers import config_validation as cv
import logging


DEFAULT_POLL_INTERVAL: int = 10
DEFAULT_FAST_POLL_INTERVAL: float = 0.75
MAX_ERRORS = 5
RETRY_INTERVAL_SECONDS = 60
DOMAIN = "lennoxs30"
_LOGGER = logging.getLogger(__name__)


STEP_ONE = vol.Schema(
    {
        vol.Required(CONF_CLOUD_CONNECTION, default=False): cv.boolean,
    }
)

STEP_CLOUD = vol.Schema(
    {
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_APP_ID): cv.string,
        vol.Optional(CONF_CREATE_SENSORS, default=True): cv.boolean,
        vol.Optional(CONF_ALLERGEN_DEFENDER_SWITCH, default=False): cv.boolean,
        vol.Optional(CONF_INIT_WAIT_TIME, default=60): cv.positive_int,
        vol.Optional(CONF_SCAN_INTERVAL, default=15): cv.positive_int,
        vol.Optional(
            CONF_FAST_POLL_INTERVAL, default=DEFAULT_FAST_POLL_INTERVAL
        ): cv.positive_float,
        vol.Optional(CONF_PII_IN_MESSAGE_LOGS, default=False): cv.boolean,
        vol.Optional(CONF_MESSAGE_DEBUG_LOGGING, default=True): cv.boolean,
        vol.Optional(CONF_LOG_MESSAGES_TO_FILE, default=False): cv.boolean,
        vol.Optional(CONF_MESSAGE_DEBUG_FILE, default=""): cv.string,
    }
)

STEP_LOCAL = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_APP_ID, default="homeassistant"): cv.string,
        vol.Optional(CONF_CREATE_SENSORS, default=True): cv.boolean,
        vol.Optional(CONF_ALLERGEN_DEFENDER_SWITCH, default=False): cv.boolean,
        vol.Optional(CONF_CREATE_INVERTER_POWER, default=False): cv.boolean,
        vol.Optional(CONF_INIT_WAIT_TIME, default=30): cv.positive_int,
        vol.Optional(CONF_SCAN_INTERVAL, default=1): cv.positive_int,
        vol.Optional(
            CONF_FAST_POLL_INTERVAL, default=DEFAULT_FAST_POLL_INTERVAL
        ): cv.positive_float,
        vol.Optional(CONF_PROTOCOL, default="https"): cv.string,
        vol.Optional(CONF_PII_IN_MESSAGE_LOGS, default=False): cv.boolean,
        vol.Optional(CONF_MESSAGE_DEBUG_LOGGING, default=True): cv.boolean,
        vol.Optional(CONF_LOG_MESSAGES_TO_FILE, default=False): cv.boolean,
        vol.Optional(CONF_MESSAGE_DEBUG_FILE, default=""): cv.string,
    }
)


def host_valid(hostport: str):
    """Return True if hostname or IP address is valid."""
    # We allow an host:port syntax.
    splits = hostport.split(":")
    host = splits[0]
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
        _LOGGER.debug(f"async_step_user user_input [{user_input}]")
        if user_input is not None:
            cloud_local = user_input[CONF_CLOUD_CONNECTION]
            if cloud_local:
                return await self.async_step_cloud(user_input=user_input)
            else:
                return await self.async_step_local(user_input=user_input)

        return self.async_show_form(step_id="user", data_schema=STEP_ONE, errors=errors)

    async def async_step_cloud(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        _LOGGER.debug(f"async_step_cloud user_input [{user_input}]")
        if user_input is not None and CONF_EMAIL in user_input:
            await self.async_set_unique_id("lennoxs30" + user_input[CONF_EMAIL])
            self._abort_if_unique_id_configured()
            user_input[CONF_CLOUD_CONNECTION] = True
            if user_input[CONF_LOG_MESSAGES_TO_FILE] == False:
                user_input[CONF_MESSAGE_DEBUG_FILE] = ""
            return self.async_create_entry(
                title=user_input[CONF_EMAIL], data=user_input
            )
        return self.async_show_form(
            step_id="cloud", data_schema=STEP_CLOUD, errors=errors
        )

    async def async_step_local(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        _LOGGER.debug(f"async_step_local user_input [{user_input}]")

        if user_input is not None and CONF_HOST in user_input:
            host = user_input[CONF_HOST]
            if host != "Cloud":
                if self._host_in_configuration_exists(host):
                    errors[CONF_HOST] = "already_configured"
                elif not host_valid(user_input[CONF_HOST]):
                    errors[CONF_HOST] = "invalid host IP"
                else:
                    await self.async_set_unique_id("lennoxs30" + user_input[CONF_HOST])
                    self._abort_if_unique_id_configured()
                    user_input[CONF_CLOUD_CONNECTION] = False
                    if user_input[CONF_LOG_MESSAGES_TO_FILE] == False:
                        user_input[CONF_MESSAGE_DEBUG_FILE] = ""

                    return self.async_create_entry(
                        title=user_input[CONF_HOST], data=user_input
                    )
        return self.async_show_form(
            step_id="local", data_schema=STEP_LOCAL, errors=errors
        )

    async def async_step_import(self, user_input) -> FlowResult:
        """Handle the import step."""
        _LOGGER.debug(f"async_step_import user_input [{user_input}]")
        await self.async_set_unique_id(user_input[CONF_HOST])
        self._abort_if_unique_id_configured()
        return await self.async_step_user(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        _LOGGER.debug(
            f"OptionsFlowHandler:async_step_init user_input [{user_input}] data [{self.config_entry.data}] options[{self.config_entry.options}]"
        )
        if user_input is not None:
            if CONF_HOST in self.config_entry.data:
                user_input[CONF_HOST] = self.config_entry.data[CONF_HOST]
            if CONF_EMAIL in self.config_entry.data:
                user_input[CONF_EMAIL] = self.config_entry.data[CONF_EMAIL]
            if CONF_CLOUD_CONNECTION in self.config_entry.data:
                user_input[CONF_CLOUD_CONNECTION] = self.config_entry.data[
                    CONF_CLOUD_CONNECTION
                ]
            if user_input[CONF_LOG_MESSAGES_TO_FILE] == False:
                user_input[CONF_MESSAGE_DEBUG_FILE] = ""

            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input, options=self.config_entry.options
            )
            return self.async_create_entry(title="", data={})

        if self.config_entry.data[CONF_CLOUD_CONNECTION] == False:
            # Local Connection
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONF_APP_ID, default=self.config_entry.data[CONF_APP_ID]
                        ): cv.string,
                        vol.Optional(
                            CONF_CREATE_SENSORS,
                            default=self.config_entry.data[CONF_CREATE_SENSORS],
                        ): cv.boolean,
                        vol.Optional(
                            CONF_ALLERGEN_DEFENDER_SWITCH,
                            default=self.config_entry.data[
                                CONF_ALLERGEN_DEFENDER_SWITCH
                            ],
                        ): cv.boolean,
                        vol.Optional(
                            CONF_CREATE_INVERTER_POWER,
                            default=self.config_entry.data[CONF_CREATE_INVERTER_POWER],
                        ): cv.boolean,
                        vol.Optional(
                            CONF_SCAN_INTERVAL,
                            default=self.config_entry.data[CONF_SCAN_INTERVAL],
                        ): cv.positive_int,
                        vol.Optional(
                            CONF_INIT_WAIT_TIME,
                            default=self.config_entry.data[CONF_INIT_WAIT_TIME],
                        ): cv.positive_int,
                        vol.Optional(
                            CONF_FAST_POLL_INTERVAL,
                            default=self.config_entry.data[CONF_FAST_POLL_INTERVAL],
                        ): cv.positive_float,
                        vol.Optional(
                            CONF_PROTOCOL, default=self.config_entry.data[CONF_PROTOCOL]
                        ): cv.string,
                        vol.Optional(
                            CONF_PII_IN_MESSAGE_LOGS,
                            default=self.config_entry.data[CONF_PII_IN_MESSAGE_LOGS],
                        ): cv.boolean,
                        vol.Optional(
                            CONF_MESSAGE_DEBUG_LOGGING,
                            default=self.config_entry.data[CONF_MESSAGE_DEBUG_LOGGING],
                        ): cv.boolean,
                        vol.Optional(
                            CONF_LOG_MESSAGES_TO_FILE,
                            default=self.config_entry.data[CONF_LOG_MESSAGES_TO_FILE],
                        ): cv.boolean,
                        vol.Optional(
                            CONF_MESSAGE_DEBUG_FILE,
                            default=self.config_entry.data[CONF_MESSAGE_DEBUG_FILE],
                        ): cv.string,
                    }
                ),
            )
        else:
            # Cloud Connection
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONF_PASSWORD,
                            default=self.config_entry.data[CONF_PASSWORD],
                        ): cv.string,
                        vol.Optional(
                            CONF_APP_ID, default=self.config_entry.data[CONF_APP_ID]
                        ): cv.string,
                        vol.Optional(
                            CONF_CREATE_SENSORS,
                            default=self.config_entry.data[CONF_CREATE_SENSORS],
                        ): cv.boolean,
                        vol.Optional(
                            CONF_ALLERGEN_DEFENDER_SWITCH,
                            default=self.config_entry.data[
                                CONF_ALLERGEN_DEFENDER_SWITCH
                            ],
                        ): cv.boolean,
                        vol.Optional(
                            CONF_SCAN_INTERVAL,
                            default=self.config_entry.data[CONF_SCAN_INTERVAL],
                        ): cv.positive_int,
                        vol.Optional(
                            CONF_INIT_WAIT_TIME,
                            default=self.config_entry.data[CONF_INIT_WAIT_TIME],
                        ): cv.positive_int,
                        vol.Optional(
                            CONF_FAST_POLL_INTERVAL,
                            default=self.config_entry.data[CONF_FAST_POLL_INTERVAL],
                        ): cv.positive_float,
                        vol.Optional(
                            CONF_PROTOCOL, default=self.config_entry.data[CONF_PROTOCOL]
                        ): cv.string,
                        vol.Optional(
                            CONF_PII_IN_MESSAGE_LOGS,
                            default=self.config_entry.data[CONF_PII_IN_MESSAGE_LOGS],
                        ): cv.boolean,
                        vol.Optional(
                            CONF_MESSAGE_DEBUG_LOGGING,
                            default=self.config_entry.data[CONF_MESSAGE_DEBUG_LOGGING],
                        ): cv.boolean,
                        vol.Optional(
                            CONF_LOG_MESSAGES_TO_FILE,
                            default=self.config_entry.data[CONF_LOG_MESSAGES_TO_FILE],
                        ): cv.boolean,
                        vol.Optional(
                            CONF_MESSAGE_DEBUG_FILE,
                            default=self.config_entry.data[CONF_MESSAGE_DEBUG_FILE],
                        ): cv.string,
                    }
                ),
            )
