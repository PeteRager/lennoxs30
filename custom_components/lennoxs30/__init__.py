"""Support for Lennoxs30 cloud api"""
import asyncio
from asyncio.locks import Event, Lock
import logging
import time

from lennoxs30api.s30exception import EC_COMMS_ERROR, EC_CONFIG_TIMEOUT

from lennoxs30api import (
    EC_HTTP_ERR,
    EC_LOGIN,
    EC_SUBSCRIBE,
    EC_UNAUTHORIZED,
    S30Exception,
    s30api_async,
    lennox_system,
)
import voluptuous as vol
from .const import (
    CONF_ALLERGEN_DEFENDER_SWITCH,
    CONF_APP_ID,
    CONF_CREATE_INVERTER_POWER,
    CONF_CREATE_DIAGNOSTICS_SENSORS,
    CONF_CREATE_PARAMETERS,
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
    LENNOX_DOMAIN,
    CONF_CLOUD_CONNECTION,
    MANAGER,
    VENTILATION_EQUIPMENT_ID,
)
from .device import (
    Device,
    S30AuxiliaryUnit,
    S30ControllerDevice,
    S30IndoorUnit,
    S30OutdoorUnit,
    S30VentilationUnit,
    S30ZoneThermostat,
)
from .util import dict_redact_fields, redact_email

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
PLATFORMS = ["sensor", "climate", "switch", "number", "binary_sensor", "select"]

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
    CONF_TIMEOUT,
)

DEFAULT_POLL_INTERVAL: int = 10
DEFAULT_LOCAL_POLL_INTERVAL: int = 1
DEFAULT_FAST_POLL_INTERVAL: float = 0.75
MAX_ERRORS = 2
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

        conf_scan_interval = config.get(DOMAIN).get(CONF_SCAN_INTERVAL)
        if conf_scan_interval is None:
            if cloud_connection == True:
                conf_scan_interval = DEFAULT_POLL_INTERVAL
            else:
                conf_scan_interval = DEFAULT_LOCAL_POLL_INTERVAL

        migration_data = {
            CONF_SCAN_INTERVAL: conf_scan_interval,
            CONF_FAST_POLL_INTERVAL: config.get(DOMAIN).get(CONF_FAST_POLL_INTERVAL),
            CONF_ALLERGEN_DEFENDER_SWITCH: config.get(DOMAIN).get(
                CONF_ALLERGEN_DEFENDER_SWITCH
            ),
            CONF_APP_ID: config.get(DOMAIN).get(CONF_APP_ID),
            CONF_INIT_WAIT_TIME: config.get(DOMAIN).get(CONF_INIT_WAIT_TIME),
            CONF_CREATE_SENSORS: config.get(DOMAIN).get(CONF_CREATE_SENSORS),
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
            migration_data[CONF_CREATE_INVERTER_POWER] = config.get(DOMAIN).get(
                CONF_CREATE_INVERTER_POWER
            )
        # Make sure when migrating YAML, that any new configuration defaults are added.
        _upgrade_config(migration_data, 1)
        create_migration_task(hass, migration_data)
    return True


def create_migration_task(hass, migration_data):
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=migration_data,
        )
    )


def _upgrade_config(config: dict, current_version: int) -> int:
    if current_version == 1:
        config[CONF_FAST_POLL_COUNT] = 10
        config[CONF_TIMEOUT] = (
            DEFAULT_CLOUD_TIMEOUT
            if config[CONF_CLOUD_CONNECTION] == True
            else DEFAULT_LOCAL_TIMEOUT
        )
        current_version = 2
    if current_version == 2:
        config[CONF_CREATE_DIAGNOSTICS_SENSORS] = False
        current_version = 3
    if current_version == 3:
        if config[CONF_CLOUD_CONNECTION] == False:
            config[CONF_CREATE_PARAMETERS] = False
        current_version = 4
    return current_version


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    _LOGGER.info(
        f"Upgrading configuration for [{config_entry.title}] from version [{config_entry.version}]"
    )
    new = {**config_entry.data}
    old_version = config_entry.version
    new_version = _upgrade_config(new, old_version)
    if new_version > old_version:
        config_entry.version = new_version
        hass.config_entries.async_update_entry(config_entry, data=new)
        _LOGGER.info(
            f"Configuration for [{config_entry.title}] upgraded from version [{old_version}] to version [{config_entry.version}]"
        )
    return True


# Track the title of the first entry, it gets the S30.State object
_first_entry_title: str = None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug(
        f"async_setup_entry UniqueID [{entry.unique_id}] Data [{dict_redact_fields(entry.data)}]"
    )

    # Determine if this is the first entry that gets S30.State.
    global _first_entry_title
    index: int = 1
    if _first_entry_title == None:
        _first_entry_title = entry.title
    if _first_entry_title == entry.title:
        index = 0

    is_cloud = entry.data[CONF_CLOUD_CONNECTION]

    create_inverter_power: bool = False
    conf_protocol: str = None
    create_diagnostic_sensors: bool = False
    create_parameters: bool = False

    if is_cloud == True:
        host_name: str = None
        email = entry.data[CONF_EMAIL]
        password = entry.data[CONF_PASSWORD]
    else:
        host_name = entry.data[CONF_HOST]
        email: str = None
        password: str = None
        create_inverter_power: bool = entry.data[CONF_CREATE_INVERTER_POWER]
        create_diagnostic_sensors = entry.data[CONF_CREATE_DIAGNOSTICS_SENSORS]
        create_parameters = entry.data[CONF_CREATE_PARAMETERS]
        conf_protocol: str = entry.data[CONF_PROTOCOL]

    if CONF_APP_ID in entry.data:
        app_id: str = entry.data[CONF_APP_ID]
    else:
        app_id: str = None

    poll_interval = entry.data[CONF_SCAN_INTERVAL]
    fast_poll_interval = entry.data[CONF_FAST_POLL_INTERVAL]
    fast_poll_count = entry.data[CONF_FAST_POLL_COUNT]
    timeout = entry.data[CONF_TIMEOUT]

    allergenDefenderSwitch = entry.data[CONF_ALLERGEN_DEFENDER_SWITCH]

    conf_init_wait_time = entry.data[CONF_INIT_WAIT_TIME]
    create_sensors = entry.data[CONF_CREATE_SENSORS]
    conf_pii_in_message_logs = entry.data[CONF_PII_IN_MESSAGE_LOGS]
    conf_message_debug_logging = entry.data[CONF_MESSAGE_DEBUG_LOGGING]
    conf_message_debug_file = entry.data[CONF_MESSAGE_DEBUG_FILE]
    # If no path specified then it goes into the config directory,
    if conf_message_debug_file == "":
        conf_message_debug_file = None

    _LOGGER.debug(
        f"async_setup starting scan_interval [{poll_interval}] fast_scan_interval[{fast_poll_interval}] app_id [{app_id}] config_init_wait_time [{conf_init_wait_time}] create_sensors [{create_sensors}] create_inverter_power [{create_inverter_power}] create_diagnostic_sensors [{create_diagnostic_sensors}] timeout [{timeout}]"
    )

    manager = Manager(
        hass=hass,
        config=entry,
        email=email,
        password=password,
        poll_interval=poll_interval,
        fast_poll_interval=fast_poll_interval,
        fast_poll_count=fast_poll_count,
        timeout=timeout,
        allergenDefenderSwitch=allergenDefenderSwitch,
        app_id=app_id,
        conf_init_wait_time=conf_init_wait_time,
        ip_address=host_name,
        create_sensors=create_sensors,
        create_inverter_power=create_inverter_power,
        protocol=conf_protocol,
        index=index,
        pii_message_logs=conf_pii_in_message_logs,
        message_debug_logging=conf_message_debug_logging,
        message_logging_file=conf_message_debug_file,
        create_diagnostic_sensors=create_diagnostic_sensors,
        create_equipment_parameters=create_parameters,
    )
    try:
        listener = hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, manager.async_shutdown
        )
        await manager.s30_initialize()
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
    _LOGGER.debug(f"async_unload_entry entry [{entry.unique_id}]")
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
        fast_poll_count: int,
        timeout: int,
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
        create_diagnostic_sensors: bool = False,
        create_equipment_parameters: bool = False,
    ):
        self._config_entry: ConfigEntry = config
        self._reinitialize: bool = False
        self._err_cnt: int = 0
        self._mp_wakeup_event: Event = Event()
        self._climate_entities_initialized: bool = False
        self._hass: HomeAssistant = hass
        self._config: ConfigEntry = config
        self._poll_interval: int = poll_interval
        self._fast_poll_interval: float = fast_poll_interval
        self._fast_poll_count: int = fast_poll_count
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
            timeout=timeout,
        )
        self._shutdown = False
        self._retrieve_task = None
        self._allergenDefenderSwitch = allergenDefenderSwitch
        self._createSensors: bool = create_sensors
        self._create_inverter_power: bool = create_inverter_power
        self._create_diagnostic_sensors: bool = create_diagnostic_sensors
        self._create_equipment_parameters: bool = create_equipment_parameters
        self._conf_init_wait_time = conf_init_wait_time
        self._is_metric: bool = hass.config.units.is_metric
        self.connected = False
        self.last_cloud_presence_poll: float = None

        self._cs_callbacks = []
        self.system_equip_device_map: dict[str, dict[int, Device]] = {}
        if index == 0:
            self.connection_state = DOMAIN_STATE
        else:
            if ip_address == None:
                e_name = email.split("@")
                redacted_email: str = e_name[0].replace(".", "_")
                self.connection_state = "lennoxs30.conn_" + redacted_email
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
        if state == DS_CONNECTED and self.connected == False:
            self.connected = True
            self.executeConnectionStateCallbacks()
        elif (
            state
            in (
                DS_RETRY_WAIT,
                DS_LOGIN_FAILED,
            )
            and self.connected == True
        ):
            self.connected = False
            self.executeConnectionStateCallbacks()
        self._hass.states.async_set(
            self.connection_state, state, self.getMetricsList(), force_update=True
        )

    def registerConnectionStateCallback(self, callbackfunc):
        self._cs_callbacks.append({"func": callbackfunc})

    def executeConnectionStateCallbacks(self):
        for callback in self._cs_callbacks:
            callbackfunc = callback["func"]
            try:
                callbackfunc(self.connected)
            except Exception as e:
                # Log and eat this exception so we can process other callbacks
                _LOGGER.exception("executeConnectionStateCallbacks - failed ")

    def getMetricsList(self):
        list = self._api.metrics.getMetricList()
        # TODO these are at the individual S30 level, when we have a device object we should move this there
        systems = self._api.getSystems()
        if len(systems) > 0:
            system: lennox_system = self._api.getSystems()[0]
            if system != None:
                list["sysUpTime"] = system.sysUpTime
                list["diagLevel"] = system.diagLevel
                list["softwareVersion"] = system.softwareVersion
                list["hostname"] = self._ip_address
                list["sibling_id"] = system.sibling_identifier
                list["sibling_ip"] = system.sibling_ipAddress
        return list

    async def s30_initialize(self):
        self.updateState(DS_CONNECTING)
        await self.connect_subscribe()
        await self.configuration_initialization()
        # Launch the message pump loop
        self._retrieve_task = asyncio.create_task(self.messagePump_task())
        # Since there is no change detection implemented to update device attributes like SW version - alwayas reinit
        await self.create_devices()
        # Only add entities the first time, on reconnect we do not need to add them again
        if self._climate_entities_initialized == False:
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
        for system in self._api._systemList:
            equip_device_map: dict[int, Device] = self.system_equip_device_map.get(
                system.sysId
            )
            if equip_device_map is None:
                equip_device_map = {}
                self.system_equip_device_map[system.sysId] = equip_device_map
            s30: S30ControllerDevice = S30ControllerDevice(
                self._hass, self._config_entry, system
            )
            s30.register_device()
            if s30.eq != None:
                equip_device_map[s30.eq.equipment_id] = s30

            if system.has_outdoor_unit:
                s30_outdoor_unit = S30OutdoorUnit(
                    self._hass, self._config_entry, system, s30
                )
                s30_outdoor_unit.register_device()
                if s30_outdoor_unit.eq != None:
                    equip_device_map[
                        s30_outdoor_unit.eq.equipment_id
                    ] = s30_outdoor_unit
            if system.has_indoor_unit:
                s30_indoor_unit = S30IndoorUnit(
                    self._hass, self._config_entry, system, s30
                )
                s30_indoor_unit.register_device()
                if s30_indoor_unit.eq != None:
                    equip_device_map[s30_indoor_unit.eq.equipment_id] = s30_indoor_unit

            for eq in system.equipment.values():
                if (
                    eq.equipment_id != 0
                    and equip_device_map.get(eq.equipment_id) == None
                ):
                    aux_unit = S30AuxiliaryUnit(
                        self._hass, self._config_entry, system, s30, eq
                    )
                    aux_unit.register_device()
                    equip_device_map[aux_unit.eq.equipment_id] = aux_unit

            if system.supports_ventilation():
                d: S30VentilationUnit = S30VentilationUnit(
                    self._hass, self._config_entry, system, s30
                )
                d.register_device()
                equip_device_map[VENTILATION_EQUIPMENT_ID] = d

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
                await self.s30_initialize()
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
        systemsWithZones = 0
        loops: int = 0
        numOfSystems = len(self._api.getSystems())
        # To speed startup, we only want to sleep when a message was not received.
        got_message: bool = True

        offline_error_logged = {}

        while systemsWithZones < numOfSystems and loops < self._conf_init_wait_time:
            _LOGGER.debug(
                f"__init__:async_setup waiting for zone config to arrive host [{self._ip_address}]  numSystems ["
                + str(numOfSystems)
                + "] systemsWithZones ["
                + str(systemsWithZones)
                + "]"
            )
            # Only take a breather if we did not get a message.
            if got_message == False:
                await asyncio.sleep(1.0)
            systemsWithZones = 0
            got_message = await self.messagePump()
            for lsystem in self._api.getSystems():
                if lsystem.cloud_status == "offline":
                    if offline_error_logged.get(lsystem.sysId) == None:
                        _LOGGER.error(
                            f"The Lennox System with id [{lsystem.sysId}] is not connected to the Lennox Cloud.  Cloud Status [{lsystem.cloud_status}].  Please check your thermostats internet connection and retry."
                        )
                        offline_error_logged[lsystem.sysId] = True
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
                    systemsWithZones += 1
            if got_message == False:
                loops += 1
        if systemsWithZones < numOfSystems:
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

    async def update_cloud_presence(self):
        if self.last_cloud_presence_poll == None:
            self.last_cloud_presence_poll = time.time()
            return
        if time.time() - self.last_cloud_presence_poll < 300.0:
            return

        self.last_cloud_presence_poll = time.time()

        for system in self._api._systemList:
            _LOGGER.debug(f"update_cloud_presence sysId [{system.sysId}]")
            old_status = system.cloud_status
            try:
                await system.update_system_online_cloud()
                new_status = system.cloud_status
                if new_status == "offline" and old_status == "online":
                    _LOGGER.error(
                        f"cloud status changed to offline for sysId [{system.sysId}] name [{system.name}]"
                    )
                elif old_status == "offline" and new_status == "online":
                    _LOGGER.info(
                        f"cloud status changed to online for sysId [{system.sysId}] name [{system.name}] - resubscribing"
                    )
                    try:
                        await self._api.subscribe(system)
                    except S30Exception as e:
                        _LOGGER.error(
                            f"update_cloud_presence resubscribe error sysid [{system.sysId}] error {e.as_string()}"
                        )
                        self._reinitialize = True
                    except Exception as e:
                        _LOGGER.exception(
                            f"update_cloud_presence resubscribe error unexpected exception sysid [{system.sysId}] error {e}"
                        )
                        self._reinitialize = True

            except S30Exception as e:
                _LOGGER.error(
                    f"update_cloud_presence sysid [{system.sysId}] error {e.as_string()}"
                )
            except Exception as e:
                _LOGGER.exception(
                    f"update_cloud_presence unexpected exception sysid [{system.sysId}] error {e}"
                )

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

            if self._api._isLANConnection == False:
                await self.update_cloud_presence()

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
                        fast_polling_cd = self._fast_poll_count

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
            # this exceeds the max consecutive error count
            elif e.error_code == EC_HTTP_ERR and self._err_cnt < MAX_ERRORS:
                _LOGGER.debug(
                    f"messagePump_task - http error host [{self._ip_address}] {e.as_string()}"
                )
            # Since the S30 will close connections and kill the subscription periodically, these errors
            # are expected.  Log as warnings
            elif e.error_code == EC_COMMS_ERROR:
                _LOGGER.warning(
                    f"messagePump_task - communication error to host [{self._ip_address}] {e.as_string()}"
                )
            else:
                _LOGGER.warning(
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
        if self._err_cnt >= MAX_ERRORS:
            _LOGGER.info(
                f"messagePump_task encountered [{self._err_cnt}] consecutive errors - reinitializing connection"
            )
            self._reinitialize = True
        if bErr is False:
            self._err_cnt = 0
        return received
