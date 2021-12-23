import ipaddress
import re
from lennoxs30api.s30exception import EC_AUTHENTICATE, EC_LOGIN, S30Exception

import voluptuous as vol
from . import Manager
from .const import (
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
    LENNOX_DEFAULT_CLOUD_APP_ID,
    LENNOX_DEFAULT_LOCAL_APP_ID,
)
from .util import dict_redact_fields, redact_email
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
        vol.Optional(CONF_APP_ID, default=LENNOX_DEFAULT_CLOUD_APP_ID): cv.string,
        vol.Optional(CONF_CREATE_SENSORS, default=True): cv.boolean,
        vol.Optional(CONF_ALLERGEN_DEFENDER_SWITCH, default=False): cv.boolean,
    }
)

STEP_LOCAL = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_APP_ID, default=LENNOX_DEFAULT_LOCAL_APP_ID): cv.string,
        vol.Optional(CONF_CREATE_SENSORS, default=True): cv.boolean,
        vol.Optional(CONF_ALLERGEN_DEFENDER_SWITCH, default=False): cv.boolean,
        vol.Optional(CONF_CREATE_INVERTER_POWER, default=False): cv.boolean,
        vol.Optional(CONF_PROTOCOL, default="https"): cv.string,
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

    def get_advanced_schema(self, is_cloud: bool):
        if is_cloud == True:
            scan_interval = 15
            conf_wait_time = 60
        else:
            scan_interval = 1
            conf_wait_time = 30
        return vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=scan_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=300)
                ),
                vol.Optional(
                    CONF_FAST_POLL_INTERVAL, default=DEFAULT_FAST_POLL_INTERVAL
                ): vol.All(vol.Coerce(float), vol.Range(min=0.25, max=300.0)),
                vol.Optional(CONF_INIT_WAIT_TIME, default=conf_wait_time): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=300)
                ),
                vol.Optional(CONF_PII_IN_MESSAGE_LOGS, default=False): cv.boolean,
                vol.Optional(CONF_MESSAGE_DEBUG_LOGGING, default=True): cv.boolean,
                vol.Optional(CONF_LOG_MESSAGES_TO_FILE, default=False): cv.boolean,
                vol.Optional(CONF_MESSAGE_DEBUG_FILE, default=""): cv.string,
            }
        )

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        self.config_input = {}
        _LOGGER.debug(f"async_step_user user_input [{dict_redact_fields(user_input)}]")
        if user_input is not None:
            cloud_local = user_input[CONF_CLOUD_CONNECTION]
            self.config_input.update(user_input)
            if cloud_local:
                return await self.async_step_cloud()
            else:
                return await self.async_step_local()

        return self.async_show_form(step_id="user", data_schema=STEP_ONE, errors=errors)

    async def async_step_cloud(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        _LOGGER.debug(f"async_step_cloud user_input [{dict_redact_fields(user_input)}]")
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN + "_" + user_input[CONF_EMAIL])
            self._abort_if_unique_id_configured()
            try:
                await self.try_to_connect(user_input)
                self.config_input.update(user_input)
                return await self.async_step_advanced()
            except S30Exception as e:
                _LOGGER.error(e.as_string())
                if e.error_code == EC_LOGIN:
                    errors["base"] = "unable_to_connect_login"
                else:
                    errors["base"] = "unable_to_connect_cloud"
        return self.async_show_form(
            step_id="cloud", data_schema=STEP_CLOUD, errors=errors
        )

    async def async_step_local(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        _LOGGER.debug(f"async_step_local user_input [{dict_redact_fields(user_input)}]")

        if user_input is not None:
            host = user_input[CONF_HOST]
            if self._host_in_configuration_exists(host):
                errors[CONF_HOST] = "already_configured"
            elif not host_valid(user_input[CONF_HOST]):
                errors[CONF_HOST] = "invalid_hostname"
            else:
                await self.async_set_unique_id(DOMAIN + "_" + user_input[CONF_HOST])
                self._abort_if_unique_id_configured()
                try:
                    await self.try_to_connect(user_input)
                    self.config_input.update(user_input)
                    return await self.async_step_advanced()
                except S30Exception as e:
                    _LOGGER.error(e.as_string())
                    errors[CONF_HOST] = "unable_to_connect_local"
        return self.async_show_form(
            step_id="local", data_schema=STEP_LOCAL, errors=errors
        )

    async def async_step_advanced(self, user_input=None):
        errors = {}
        _LOGGER.debug(
            f"async_step_advanced user_input [{dict_redact_fields(user_input)}]"
        )

        if user_input is not None:
            self.config_input.update(user_input)
            return await self.create_entry()
        return self.async_show_form(
            step_id="advanced",
            data_schema=self.get_advanced_schema(
                self.config_input[CONF_CLOUD_CONNECTION]
            ),
            errors=errors,
        )

    async def create_entry(self):
        if self.config_input[CONF_CLOUD_CONNECTION] == True:
            title = redact_email(self.config_input[CONF_EMAIL])
        else:
            title = self.config_input[CONF_HOST]
        await self.async_set_unique_id(DOMAIN + "_" + title)
        self._abort_if_unique_id_configured()
        if self.config_input[CONF_LOG_MESSAGES_TO_FILE] == False:
            self.config_input[CONF_MESSAGE_DEBUG_FILE] = ""
        _LOGGER.debug(
            f"async_step_advanced config_input [{dict_redact_fields(self.config_input)}]"
        )
        return self.async_create_entry(title=title, data=self.config_input)

    async def try_to_connect(self, user_input):
        if self.config_input[CONF_CLOUD_CONNECTION] == True:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]
            ip_address = None
            protocol = "https"
        else:
            email = None
            password = None
            ip_address = user_input[CONF_HOST]
            protocol = user_input[CONF_PROTOCOL]

        manager = Manager(
            hass=self.hass,
            config=None,
            email=email,
            password=password,
            poll_interval=1,
            fast_poll_interval=1.0,
            allergenDefenderSwitch=False,
            app_id=user_input[CONF_APP_ID],
            conf_init_wait_time=30,
            ip_address=ip_address,
            create_sensors=False,
            create_inverter_power=False,
            protocol=protocol,
            pii_message_logs=False,
            message_debug_logging=True,
            message_logging_file=None,
        )
        await manager.connect()
        await manager.async_shutdown(None)

    async def async_step_import(self, user_input) -> FlowResult:
        """Handle the import step."""
        self.config_input = {}
        _LOGGER.debug(
            f"async_step_import user_input [{dict_redact_fields(user_input)}]"
        )
        self.config_input.update(user_input)
        return await self.create_entry()

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
            f"OptionsFlowHandler:async_step_init user_input [{dict_redact_fields(user_input)}] data [{dict_redact_fields(self.config_entry.data)}]"
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
                        ): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
                        vol.Optional(
                            CONF_INIT_WAIT_TIME,
                            default=self.config_entry.data[CONF_INIT_WAIT_TIME],
                        ): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
                        vol.Optional(
                            CONF_FAST_POLL_INTERVAL,
                            default=self.config_entry.data[CONF_FAST_POLL_INTERVAL],
                        ): vol.All(vol.Coerce(float), vol.Range(min=0.25, max=300.0)),
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
                        ): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
                        vol.Optional(
                            CONF_INIT_WAIT_TIME,
                            default=self.config_entry.data[CONF_INIT_WAIT_TIME],
                        ): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
                        vol.Optional(
                            CONF_FAST_POLL_INTERVAL,
                            default=self.config_entry.data[CONF_FAST_POLL_INTERVAL],
                        ): vol.All(vol.Coerce(float), vol.Range(min=0.25, max=300.0)),
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
