import logging
import asyncio
from . import s30api_async
#
DOMAIN = "lennoxs30"
#
_LOGGER = logging.getLogger(__name__)
#
from homeassistant.const import (CONF_EMAIL, CONF_PASSWORD)
#



async def async_setup(hass, config):
    hass.states.async_set("lennox30.state", "Running")
    _LOGGER.info("__init__:async_setup config")

    email = config.get(DOMAIN).get(CONF_EMAIL)
    password = config.get(DOMAIN).get(CONF_PASSWORD)

    s30api = s30api_async.s30api_async(email, password)

    if await s30api.serverConnect() == False:
        _LOGGER.error("__init__:async_setup connection failed")
        return False

    for lsystem in s30api.getSystems():
        if await s30api.subscribe(lsystem) == False:
            _LOGGER.error("__init__:async_setup config Data Subscription Failed lsystem [" + lsystem.sysId + "]")
            return False
    
    # Wait for zones to appear on each system
    sytemsWithZones = 0
    numOfSystems = len(s30api.getSystems())
    while (sytemsWithZones < numOfSystems):
        _LOGGER.debug("__init__:async_setup waiting for zone config to arrive numSystems [" + str(numOfSystems) + "] sytemsWithZonze [" + str(sytemsWithZones) + "]")
        sytemsWithZones = 0
        await asyncio.sleep(1)
        await s30api.retrieve()
        for lsystem in s30api.getSystems():
                numZones = len(lsystem.getZoneList())
                _LOGGER.debug("__init__:async_setup wait for zones system [" + lsystem.sysId + "] numZone [" + str(numZones) + "]")
                if numZones > 0:
                    sytemsWithZones += 1

    # Launch the retrieve loop
    asyncio.create_task(retrieve_task(s30api))

    hass.helpers.discovery.load_platform('climate', DOMAIN, s30api, config)
    return True

async def retrieve_task(s30api):
    # TODO figure out a way to shutdown
    await asyncio.sleep(10)
    for system in s30api.getSystems():
        system.enableCallbackProcessing(True)
    while (True):
        try:
            _LOGGER.debug("retrieve_task running")
            await s30api.retrieve()
            await asyncio.sleep(10)
        except Exception as e:
            _LOGGER.error("requestDataHelper - Exception " + str(e))
            return False

