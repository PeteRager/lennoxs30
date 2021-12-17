"""Support for Lennoxs30 cloud api"""
import asyncio
from asyncio.locks import Event, Lock
import logging

from lennoxs30api.s30exception import EC_COMMS_ERROR, EC_CONFIG_TIMEOUT

from lennoxs30api import (
    EC_HTTP_ERR,
    EC_LOGIN,
    EC_SUBSCRIBE,
    EC_UNAUTHORIZED,
    S30Exception,
    s30api_async,
)
import voluptuous as vol
from config.custom_components.lennoxs30.const import (
    CONF_ALLERGEN_DEFENDER_SWITCH,
    CONF_APP_ID,
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
    LENNOX_DOMAIN,
    CONF_CLOUD_CONNECTION,
    MANAGER,
)
from config.custom_components.lennoxs30.device import (
    S30ControllerDevice,
    S30OutdoorUnit,
    S30ZoneThermostat,
)
from config.custom_components.lennoxs30.util import dict_redact_fields

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from typing import Any

DOMAIN = LENNOX_DOMAIN
DOMAIN_STATE = "lennoxs30.state"
PLATFORMS = ["sensor", "climate", "switch", "number"]


DS_CONNECTING = "Connecting"
DS_DISCONNECTED = "Disconnected"
DS_LOGIN_FAILED = "Login Failed"
DS_CONNECTED = "Connected"
DS_RETRY_WAIT = "Waiting to Retry"
DS_FAILED = "Failed"

from homeassistant.const import (
    CONF_HOST,
    CONF_EMAIL,
    CONF_HOSTS,
    CONF_PASSWORD,
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    EVENT_HOMEASSISTANT_STOP,
)

DEFAULT_POLL_INTERVAL: int = 10
DEFAULT_LOCAL_POLL_INTERVAL: int = 1
DEFAULT_FAST_POLL_INTERVAL: float = 0.75
MAX_ERRORS = 5
RETRY_INTERVAL_SECONDS = 60

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_EMAIL): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_HOSTS, default="Cloud"): str,
                vol.Optional(CONF_SCAN_INTERVAL): cv.positive_int,
                vol.Optional(
                    CONF_FAST_POLL_INTERVAL, default=DEFAULT_FAST_POLL_INTERVAL
                ): cv.positive_float,
                vol.Optional(CONF_ALLERGEN_DEFENDER_SWITCH, default=False): cv.boolean,
                vol.Optional(CONF_APP_ID): cv.string,
                vol.Optional(CONF_INIT_WAIT_TIME, default=30): cv.positive_int,
                vol.Optional(CONF_CREATE_SENSORS, default=False): cv.boolean,
                vol.Optional(CONF_CREATE_INVERTER_POWER, default=False): cv.boolean,
                vol.Optional(CONF_PROTOCOL, default="https"): cv.string,
                vol.Optional(CONF_PII_IN_MESSAGE_LOGS, default=False): cv.boolean,
                vol.Optional(CONF_MESSAGE_DEBUG_LOGGING, default=True): cv.boolean,
                vol.Optional(CONF_MESSAGE_DEBUG_FILE, default=""): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Import config as config entry."""
    hass.data[DOMAIN] = {}
    if config.get(DOMAIN) is None:
        return True

    _LOGGER.warning(
        "Configuration of the LennoxS30 platform in YAML is deprecated "
        "and will be removed; Your existing configuration "
        "has been imported into the UI automatically and can be safely removed "
        "from your configuration.yaml file"
    )
    conf_hosts: str = config.get(DOMAIN).get(CONF_HOSTS)
    host_list = []
    if conf_hosts == "Cloud":
        conf_hosts = None
        host_list.append(None)
    else:
        host_list = conf_hosts.split(",")

    for host_name in host_list:
        cloud_connection: bool = False
        if host_name == None:
            cloud_connection = True
        log_to_file = True
        if config.get(DOMAIN).get(CONF_MESSAGE_DEBUG_FILE) == "":
            log_to_file = False

        migration_data = {
            CONF_SCAN_INTERVAL: config.get(DOMAIN).get(CONF_SCAN_INTERVAL),
            CONF_FAST_POLL_INTERVAL: config.get(DOMAIN).get(CONF_FAST_POLL_INTERVAL),
            CONF_ALLERGEN_DEFENDER_SWITCH: config.get(DOMAIN).get(
                CONF_ALLERGEN_DEFENDER_SWITCH
            ),
            CONF_APP_ID: config.get(DOMAIN).get(CONF_APP_ID),
            CONF_INIT_WAIT_TIME: config.get(DOMAIN).get(CONF_INIT_WAIT_TIME),
            CONF_CREATE_SENSORS: config.get(DOMAIN).get(CONF_CREATE_SENSORS),
            CONF_CREATE_INVERTER_POWER: config.get(DOMAIN).get(
                CONF_CREATE_INVERTER_POWER
            ),
            CONF_PROTOCOL: config.get(DOMAIN).get(CONF_PROTOCOL),
            CONF_PII_IN_MESSAGE_LOGS: config.get(DOMAIN).get(CONF_PII_IN_MESSAGE_LOGS),
            CONF_MESSAGE_DEBUG_LOGGING: config.get(DOMAIN).get(
                CONF_MESSAGE_DEBUG_LOGGING
            ),
            CONF_MESSAGE_DEBUG_FILE: config.get(DOMAIN).get(CONF_MESSAGE_DEBUG_FILE),
            CONF_LOG_MESSAGES_TO_FILE: log_to_file,
            CONF_CLOUD_CONNECTION: cloud_connection,
        }

        if cloud_connection == True:
            migration_data[CONF_EMAIL] = config.get(DOMAIN).get(CONF_EMAIL)
            migration_data[CONF_PASSWORD] = config.get(DOMAIN).get(CONF_PASSWORD)
            if migration_data[CONF_APP_ID] == None:
                migration_data[CONF_APP_ID] = LENNOX_DEFAULT_CLOUD_APP_ID
        else:
            migration_data[CONF_HOST] = host_name
            if migration_data[CONF_APP_ID] == None:
                migration_data[CONF_APP_ID] = LENNOX_DEFAULT_LOCAL_APP_ID

        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=migration_data,
            )
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug(
        f"async_setup_entry UniqueID [{entry.unique_id}] Data [{dict_redact_fields(entry.data)}]"
    )
    is_cloud = entry.data[CONF_CLOUD_CONNECTION]
    if is_cloud == True:
        host_name: str = None
        email = entry.data[CONF_EMAIL]
        password = entry.data[CONF_PASSWORD]
        create_inverter_power: bool = False
        conf_protocol: str = None
    else:
        host_name = entry.data[CONF_HOST]
        email: str = None
        password: str = None
        create_inverter_power: bool = entry.data[CONF_CREATE_INVERTER_POWER]
        conf_protocol: str = entry.data[CONF_PROTOCOL]

    if CONF_APP_ID in entry.data:
        app_id: str = entry.data[CONF_APP_ID]
    else:
        app_id: str = None

    t = None
    if CONF_SCAN_INTERVAL in entry.data:
        t = entry.data[CONF_SCAN_INTERVAL]
    if t != None and t > 0:
        poll_interval = t
    else:
        if host_name == None:
            poll_interval = DEFAULT_POLL_INTERVAL
        else:
            poll_interval = DEFAULT_LOCAL_POLL_INTERVAL

    t = None
    if CONF_FAST_POLL_INTERVAL in entry.data:
        t = entry.data[CONF_FAST_POLL_INTERVAL]
    if t != None and t > 0.2:
        fast_poll_interval = t
    else:
        fast_poll_interval = DEFAULT_FAST_POLL_INTERVAL
    allergenDefenderSwitch = entry.data[CONF_ALLERGEN_DEFENDER_SWITCH]

    conf_init_wait_time = entry.data[CONF_INIT_WAIT_TIME]
    create_sensors = entry.data[CONF_CREATE_SENSORS]
    conf_pii_in_message_logs = entry.data[CONF_PII_IN_MESSAGE_LOGS]
    conf_message_debug_logging = entry.data[CONF_MESSAGE_DEBUG_LOGGING]
    conf_message_debug_file = entry.data[CONF_MESSAGE_DEBUG_FILE]
    if conf_message_debug_file == "":
        conf_message_debug_file = None
    _LOGGER.debug(
        f"async_setup starting scan_interval [{poll_interval}] fast_scan_interval[{fast_poll_interval}] app_id [{app_id}] config_init_wait_time [{conf_init_wait_time}] create_sensors [{create_sensors}] create_inverter_power [{create_inverter_power}]"
    )

    manager = Manager(
        hass=hass,
        config=entry,
        email=email,
        password=password,
        poll_interval=poll_interval,
        fast_poll_interval=fast_poll_interval,
        allergenDefenderSwitch=allergenDefenderSwitch,
        app_id=app_id,
        conf_init_wait_time=conf_init_wait_time,
        ip_address=host_name,
        create_sensors=create_sensors,
        create_inverter_power=create_inverter_power,
        protocol=conf_protocol,
        index=0,
        pii_message_logs=conf_pii_in_message_logs,
        message_debug_logging=conf_message_debug_logging,
        message_logging_file=conf_message_debug_file,
        config_entry=entry,
    )
    try:
        listener = hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, manager.async_shutdown
        )
        await manager.s30_initalize()
    except S30Exception as e:
        if e.error_code == EC_LOGIN:
            # TODO: encapsulate in manager class
            manager.updateState(DS_LOGIN_FAILED)
            raise HomeAssistantError(
                f"Lennox30 unable to login host [{host_name}] - please check credentials and restart Home Assistant"
            )
        elif e.error_code == EC_CONFIG_TIMEOUT:
            _LOGGER.warning("async_setup: " + e.message)
            _LOGGER.info("connection will be retried in 1 minute")
            asyncio.create_task(manager.initialize_retry_task())
        else:
            _LOGGER.error("async_setup unexpected error " + e.message)
            _LOGGER.info("connection will be retried in 1 minute")
            asyncio.create_task(manager.initialize_retry_task())
    _LOGGER.debug(f"async_setup complete host [{host_name}]")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug(f"async_unlod_entry entry [{entry.unique_id}]")
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok == True:
        entry_data = hass.data[DOMAIN].pop(entry.unique_id)
        manager: Manager = entry_data[MANAGER]
        try:
            await manager.async_shutdown(None)
        except S30Exception as e:
            _LOGGER.error(
                f"async_unload_entry entry [{entry.unique_id}] error [{e.as_string()}]"
            )
        except Exception as e:
            _LOGGER.exception(f"async_unload_entry entry [{entry.unique_id}]")
        return True
    else:
        _LOGGER.error(
            f"async_unload_entry call to hass.config_entries.async_unload_platforms returned False"
        )
        return False


class Manager(object):
    def __init__(
        self,
        hass: HomeAssistant,
        config: ConfigEntry,
        email: str,
        password: str,
        poll_interval: int,
        fast_poll_interval: float,
        allergenDefenderSwitch: bool,
        app_id: str,
        conf_init_wait_time: int,
        ip_address: str,
        create_sensors: bool,
        create_inverter_power: bool,
        protocol: str,
        index: int = 0,
        pii_message_logs: bool = False,
        message_debug_logging: bool = True,
        message_logging_file: str = None,
        config_entry: ConfigEntry = None,
    ):
        self._config_entry: ConfigEntry = config_entry
        self._reinitialize: bool = False
        self._err_cnt: int = 0
        self._mp_wakeup_event: Event = Event()
        self._climate_entities_initialized: bool = False
        self._hass: HomeAssistant = hass
        self._config: ConfigEntry = config
        self._poll_interval: int = poll_interval
        self._fast_poll_interval: float = fast_poll_interval
        self._protocol = protocol
        self._ip_address = ip_address
        self._pii_message_log = pii_message_logs
        self._message_debug_logging = message_debug_logging
        self._message_logging_file = message_logging_file
        self._api: s30api_async = s30api_async(
            email,
            password,
            app_id,
            ip_address=ip_address,
            protocol=self._protocol,
            pii_message_logs=self._pii_message_log,
            message_debug_logging=self._message_debug_logging,
            message_logging_file=self._message_logging_file,
        )
        self._shutdown = False
        self._retrieve_task = None
        self._allergenDefenderSwitch = allergenDefenderSwitch
        self._createSensors: bool = create_sensors
        self._create_inverter_power: bool = create_inverter_power
        self._conf_init_wait_time = conf_init_wait_time
        self._is_metric: bool = hass.config.units.is_metric
        if ip_address == None:
            self.connection_state = "lennoxs30.conn_" + email.replace(".", "_").replace(
                "@", "_"
            )
        else:
            self.connection_state = "lennoxs30.conn_" + self._ip_address.replace(
                ".", "_"
            ).replace(":", "_")

    async def async_shutdown(self, event: Event) -> None:
        _LOGGER.debug(f"async_shutdown started host [{self._ip_address}]")
        self._shutdown = True
        if self._retrieve_task != None:
            self._mp_wakeup_event.set()
            await self._retrieve_task
        await self._api.shutdown()
        _LOGGER.debug(f"async_shutdown complete [{self._ip_address}]")

    def updateState(self, state: int) -> None:
        self._hass.states.async_set(
            self.connection_state, state, self.getMetricsList(), force_update=True
        )

    def getMetricsList(self):
        list = self._api.metrics.getMetricList()
        # TODO these are at the individual S30 level, when we have a device object we should move this there
        systems = self._api.getSystems()
        if len(systems) > 0:
            system: s30api_async.lennox_system = self._api.getSystems()[0]
            if system != None:
                list["sysUpTime"] = system.sysUpTime
                list["diagLevel"] = system.diagLevel
                list["softwareVersion"] = system.softwareVersion
                list["hostname"] = self._ip_address
        return list

    async def s30_initalize(self):
        self.updateState(DS_CONNECTING)
        await self.connect_subscribe()
        await self.configuration_initialization()
        # Launch the message pump loop
        self._retrieve_task = asyncio.create_task(self.messagePump_task())
        # Only add entities the first time, on reconnect we do not need to add them again
        if self._climate_entities_initialized == False:
            await self.create_devices()
            self._hass.data[DOMAIN][self._config.unique_id] = {MANAGER: self}
            for platform in PLATFORMS:
                self._hass.async_create_task(
                    self._hass.config_entries.async_forward_entry_setup(
                        self._config, platform
                    )
                )
            self._climate_entities_initialized = True
        self.updateState(DS_CONNECTED)

    async def create_devices(self):
        self.s30_devices = {}
        self.s30_outdoorunits = {}
        for system in self._api._systemList:
            s30: S30ControllerDevice = S30ControllerDevice(
                self._hass, self._config_entry, system
            )
            s30.register_device()
            self.s30_devices[system.sysId] = s30
            s30_outdoor_unit = S30OutdoorUnit(
                self._hass, self._config_entry, system, s30
            )
            s30_outdoor_unit.register_device()
            self.s30_outdoorunits[system.sysId] = s30_outdoor_unit
            for zone in system._zoneList:
                if zone.is_zone_active() == True:
                    z: S30ZoneThermostat = S30ZoneThermostat(
                        self._hass, self._config_entry, system, zone, s30
                    )
                    z.register_device()

    async def initialize_retry_task(self):
        while True:
            self.updateState(DS_RETRY_WAIT)
            await asyncio.sleep(RETRY_INTERVAL_SECONDS)
            self.updateState(DS_CONNECTING)
            try:
                await self.s30_initalize()
                self.updateState(DS_CONNECTED)
                return

            except S30Exception as e:
                if e.error_code == EC_LOGIN:
                    # TODO: encapsulate in manager class
                    self.updateState(DS_LOGIN_FAILED)
                    _LOGGER.error(
                        f"initialize_retry_task host [{self._ip_address}] {e.as_string()}"
                    )
                    return
                elif e.error_code == EC_CONFIG_TIMEOUT:
                    _LOGGER.warning(
                        f"async_setup: host [{self._ip_address}] {e.as_string()}"
                    )
                    _LOGGER.info(
                        f"connection host [{self._ip_address}] will be retried in 1 minute"
                    )
                else:
                    _LOGGER.error(
                        f"async_setup host [{self._ip_address}] unexpected error {e.as_string()}"
                    )
                    _LOGGER.info(
                        f"async setup host [{self._ip_address}] will be retried in 1 minute"
                    )

    async def configuration_initialization(self) -> None:
        # Wait for zones to appear on each system
        sytemsWithZones = 0
        loops: int = 0
        numOfSystems = len(self._api.getSystems())
        while sytemsWithZones < numOfSystems and loops < self._conf_init_wait_time:
            _LOGGER.debug(
                f"__init__:async_setup waiting for zone config to arrive host [{self._ip_address}]  numSystems ["
                + str(numOfSystems)
                + "] sytemsWithZones ["
                + str(sytemsWithZones)
                + "]"
            )
            sytemsWithZones = 0
            await asyncio.sleep(1.0)
            await self.messagePump()
            for lsystem in self._api.getSystems():
                # Issue #33 - system configuration isn't complete until we've received the name from Lennox.
                if lsystem.config_complete() == False:
                    continue
                numZones = len(lsystem.getZoneList())
                _LOGGER.debug(
                    f"__init__:async_setup host [{self._ip_address}] wait for zones system ["
                    + lsystem.sysId
                    + "] numZone ["
                    + str(numZones)
                    + "]"
                )
                if numZones > 0:
                    sytemsWithZones += 1
            loops += 1
        if sytemsWithZones < numOfSystems:
            raise S30Exception(
                "Timeout waiting for configuration data from Lennox - this sometimes happens, the connection will be automatically retried.  Consult the readme for more details",
                EC_CONFIG_TIMEOUT,
                1,
            )

    async def connect(self):
        await self._api.serverConnect()

    async def connect_subscribe(self):
        await self._api.serverConnect()

        for lsystem in self._api.getSystems():
            await self._api.subscribe(lsystem)

    async def reinitialize_task(self) -> None:
        while True:
            try:
                self.updateState(DS_CONNECTING)
                _LOGGER.debug(
                    f"reinitialize_task host [{self._ip_address}] - trying reconnect"
                )
                await self.connect_subscribe()
                self.updateState(DS_CONNECTED)
                break
            except S30Exception as e:
                _LOGGER.error(
                    f"reinitialize_task host [{self._ip_address}] {e.as_string()}"
                )
                if e.error_code == EC_LOGIN:
                    raise HomeAssistantError(
                        f"Lennox30 unable to login host [{self._ip_address}]  - please check credentials and restart Home Assistant"
                    )
            self.updateState(DS_RETRY_WAIT)
            await asyncio.sleep(RETRY_INTERVAL_SECONDS)

        _LOGGER.debug(
            f"reinitialize_task host [{self._ip_address}] - reconnect successful"
        )
        asyncio.create_task(self.messagePump_task())

    async def event_wait_mp_wakeup(self, timeout: float) -> bool:
        # suppress TimeoutError because we'll return False in case of timeout
        try:
            await asyncio.wait_for(self._mp_wakeup_event.wait(), timeout)
        except asyncio.TimeoutError as e:
            return False
        return self._mp_wakeup_event.is_set()

    async def messagePump_task(self) -> None:
        await asyncio.sleep(self._poll_interval)
        self._reinitialize = False
        self._err_cnt = 0
        fast_polling: bool = False
        fast_polling_cd: int = 0
        received = False
        while self._reinitialize == False:
            try:
                received = await self.messagePump()
            except Exception as e:
                _LOGGER.error(
                    f"messagePump_task host [{self._ip_address}] unexpected exception:"
                    + str(e)
                )
            if fast_polling == True:
                fast_polling_cd = fast_polling_cd - 1
                if fast_polling_cd <= 0:
                    fast_polling = False

            if self._shutdown == True:
                break

            if not received:
                if fast_polling == True:
                    res = await asyncio.sleep(
                        min(self._fast_poll_interval, self._poll_interval)
                    )
                else:
                    res = await self.event_wait_mp_wakeup(self._poll_interval)
                    if res == True:
                        self._mp_wakeup_event.clear()
                        fast_polling = True
                        fast_polling_cd = 10

        if self._shutdown == True:
            _LOGGER.debug(
                f"messagePump_task host [{self._ip_address}] is exiting to shutdown"
            )
            return
        elif self._reinitialize == True:
            self.updateState(DS_DISCONNECTED)
            asyncio.create_task(self.reinitialize_task())
            _LOGGER.debug(
                f"messagePump_task host [{self._ip_address}] is exiting - to enter retries"
            )
        else:
            _LOGGER.debug(
                f"messagePump_task host [{self._ip_address}] is exiting - and this should not happen"
            )

    async def messagePump(self) -> bool:
        bErr = False
        received = False
        try:
            _LOGGER.debug(f"messagePump_task host [{self._ip_address}] running")
            received = await self._api.messagePump()
            self.updateState(DS_CONNECTED)
        except S30Exception as e:
            self._err_cnt += 1
            # This should mean we have been logged out and need to start the login process
            if e.error_code == EC_UNAUTHORIZED:
                _LOGGER.debug(
                    f"messagePump_task host [{self._ip_address}] - unauthorized - trying to relogin"
                )
                self._reinitialize = True
            # If its an HTTP error, we will not log an error, just and info message, unless
            # this exeeeds the max consecutive error count
            elif e.error_code == EC_HTTP_ERR and self._err_cnt < MAX_ERRORS:
                _LOGGER.debug(
                    f"messagePump_task - http error host [{self._ip_address}] {e.as_string()}"
                )
            elif e.error_code == EC_COMMS_ERROR:
                _LOGGER.error(
                    f"messagePump_task - communication error to host [{self._ip_address}] {e.as_string()}"
                )
            else:
                _LOGGER.error(
                    f"messagePump_task - general error host [{self._ip_address}] {e.as_string()}"
                )
            bErr = True
        except Exception as e:
            _LOGGER.exception(
                f"messagePump_task unexpected exception host [{self._ip_address}]"
            )
            self._err_cnt += 1
            bErr = True
        # Keep retrying retrive up until we get this number of errors in a row, at which point will try to reconnect
        if self._err_cnt > MAX_ERRORS:
            self._reinitialize = True
        if bErr is False:
            self._err_cnt = 0
        return received
