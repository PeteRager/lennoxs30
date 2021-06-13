from asyncio.locks import Lock
from homeassistant.helpers.typing import ConfigType
from homeassistant.core import HomeAssistant
from homeassistant.components.lennoxs30.api.s30exception import EC_HTTP_ERR, EC_LOGIN, EC_UNAUTHORIZED, S30Exception
from homeassistant.exceptions import HomeAssistantError
import logging
import asyncio
from .api import s30api_async
#
DOMAIN = "lennoxs30"
DOMAIN_STATE = "lennoxs30.state"

DS_CONNECTING = "Connecting"
DS_DISCONNECTED = "Disconnected"
DS_LOGIN_FAILED = "Login Failed"
DS_CONNECTED = "Connected"
DS_RETRY_WAIT = "Waiting to Retry"
DS_FAILED = "Failed"

#
_LOGGER = logging.getLogger(__name__)
#
from homeassistant.const import (CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL)
#

CONF_FAST_POLL_INTERVAL = "fast_scan_interval"

MAX_ERRORS = 5
RETRY_INTERVAL_SECONDS = 60
_poll_interval:int = 10
_fast_poll_interval:float = 0.5

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    email = config.get(DOMAIN).get(CONF_EMAIL)
    password = config.get(DOMAIN).get(CONF_PASSWORD)
    t = config.get(DOMAIN).get(CONF_SCAN_INTERVAL)
    if t != None:
        _poll_interval = t
    t = config.get(DOMAIN).get(CONF_FAST_POLL_INTERVAL)
    if t != None:
        _fast_poll_interval = t
    _LOGGER.info(f"async_setup starting scan_interval [{_poll_interval}] fast_scan_interval[{_fast_poll_interval}]")

    manager = Manager(hass, config, email, password, _poll_interval, _fast_poll_interval)
    try:
        await manager.s30_initalize()
    except S30Exception as e:
        _LOGGER.error("async_setup: " + str(e))
        if e.error_code == EC_LOGIN:
            # TODO: encapsulate in manager class
            manager.updateState(DS_LOGIN_FAILED)
            raise HomeAssistantError("Lennox30 unable to login - please check credentials and restart Home Assistant")
        _LOGGER.info("retying initialization")
        asyncio.create_task(manager.initialize_retry_task())
        return False
    
    
    _LOGGER.info("async_setup complete")
    return True

class Manager(object):
    _hass: HomeAssistant = None
    _config: ConfigType = None
    _api: s30api_async.s30api_async = None
    _poll_interval:int = None
    _fast_poll_interval = None

    _reinitialize: bool = False
    _err_cnt: int = 0
    _update_counter: int = 0
    _mp_lock: Lock = Lock()


    def __init__(self, hass: HomeAssistant, config: ConfigType,  email: str, password: str, poll_interval:int, fast_poll_interval:float):
        self._hass = hass
        self._config = config
        self._poll_interval = poll_interval
        self._fast_poll_interval = fast_poll_interval
        self._api = s30api_async.s30api_async(email, password)

    def updateState(self, state: int) -> None:
        self._hass.states.async_set(DOMAIN_STATE, state, self.getMetricsList(), force_update=True)

    def getMetricsList(self):
        return self._api.metrics.getMetricList()
 
    async def s30_initalize(self):
        self.updateState(DS_CONNECTING)
        await self.connect_subscribe()
        await self.configuration_initialization()
        # Launch the message pump loop
        asyncio.create_task(self.messagePump_task())
        # TODO - this should not be run on the second time!!!!
        self._hass.helpers.discovery.load_platform('climate', DOMAIN, self._api, self._config)
        self.updateState(DS_CONNECTED)

    async def initialize_retry_task(self):
        while (True):
            self.updateState(DS_RETRY_WAIT)
            await asyncio.sleep(RETRY_INTERVAL_SECONDS)
            self.updateState(DS_CONNECTING)
            try:
                await self.s30_initalize()
                self.updateState(DS_CONNECTED)
            except S30Exception as e:
                _LOGGER.error("async_setup: " + str(e))
                if e.error_code == EC_LOGIN:
                    self.updateState(DS_LOGIN_FAILED)
                    raise HomeAssistantError("Lennox30 unable to login - please check credentials and restart Home Assistant")
                _LOGGER.info("retying initialization")
                self.updateState(DS_RETRY_WAIT)

    async def configuration_initialization(self) ->None:
        # Wait for zones to appear on each system
        sytemsWithZones = 0
        numOfSystems = len(self._api.getSystems())
        while (sytemsWithZones < numOfSystems):
            # TODO - should add a timeout and spin the APPLICATION_ID
            _LOGGER.debug("__init__:async_setup waiting for zone config to arrive numSystems [" + str(numOfSystems) + "] sytemsWithZones [" + str(sytemsWithZones) + "]")
            sytemsWithZones = 0
            await asyncio.sleep(1)
            await self._api.messagePump()
            for lsystem in self._api.getSystems():
                    numZones = len(lsystem.getZoneList())
                    _LOGGER.debug("__init__:async_setup wait for zones system [" + lsystem.sysId + "] numZone [" + str(numZones) + "]")
                    if numZones > 0:
                        sytemsWithZones += 1

    async def connect_subscribe(self):
        await self._api.serverConnect()

        for lsystem in self._api.getSystems():
            await self._api.subscribe(lsystem)

    async def reinitialize_task(self) -> None:
        while True:
            try:
                self.updateState(DS_CONNECTING)
                _LOGGER.info("reinitialize_task - trying reconnect")
                await self.connect_subscribe()
                self.updateState(DS_CONNECTED)
                break
            except S30Exception as e:
                _LOGGER.error("reinitialize_task: " + str(e))
                if e.error_code == EC_LOGIN:
                    raise HomeAssistantError("Lennox30 unable to login - please check credentials and restart Home Assistant")
            self.updateState(DS_RETRY_WAIT)
            await asyncio.sleep(RETRY_INTERVAL_SECONDS)

        _LOGGER.info("reinitialize_task - reconnect successful")
        asyncio.create_task(self.messagePump_task())


    async def messagePump_task(self) -> None:
        # TODO figure out a way to shutdown
        await asyncio.sleep(self._poll_interval)
        self._reinitialize = False
        self._err_cnt = 0
        self._update_counter = 0
        while self._reinitialize == False:
            try:
               await self.messagePump()
            except Exception as e:
                _LOGGER.error("messagePump_task unexpected exception:" + str(e))
            await asyncio.sleep(self._poll_interval)

        if self._reinitialize == True:            
            self.updateState(DS_DISCONNECTED)
            asyncio.create_task(self.reinitialize_task())
            _LOGGER.info("messagePump_task is exiting - to enter retries")
        else:
            _LOGGER.info("messagePump_task is exiting - and this should not happen")

    async def messagePump(self) -> bool:
        bErr = False
        # Sinc this function can be called within the messagepump_task or via
        # fast polling, we likely don't want to be in this section of code twice
        # or do we?   Not sure if this can cause a deadlock TODO
        async with self._mp_lock:
            try:
                self._update_counter += 1
                _LOGGER.debug("messagePump_task running")
                await self._api.messagePump()
                if (self._update_counter >= 6):
                    self.updateState(DS_CONNECTED)
                    self._update_counter = 0
            except S30Exception as e:
                self._err_cnt += 1
                # This should mean we have been logged out and need to start the login process
                if e.error_code == EC_UNAUTHORIZED:
                    _LOGGER.info("messagePump_task - unauthorized - trying to relogin")
                    self._reinitialize = True
                # If its an HTTP error, we will not log an error, just and info message, unless
                # this exeeeds the max consecutive error count
                elif e.error_code == EC_HTTP_ERR and self._err_cnt < MAX_ERRORS:
                    _LOGGER.info("messagePump_task - S30Exception " + str(e))
                else:
                    _LOGGER.error("messagePump_task - S30Exception " + str(e))
                bErr = True
            except Exception as e:          
                _LOGGER.error("messagePump_task - Exception " + str(e))
                self._err_cnt += 1
                bErr = True
            # Keep retrying retrive up until we get this number of errors in a row, at which point will try to reconnect
            if self._err_cnt > MAX_ERRORS:
                self._reinitialize = True
            if bErr is False:
                self._err_cnt = 0
            return bErr
 

