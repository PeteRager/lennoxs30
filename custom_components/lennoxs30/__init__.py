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
    print("async_setup config [" + str(config) + "]")

    email = config.get(DOMAIN).get(CONF_EMAIL)
    password = config.get(DOMAIN).get(CONF_PASSWORD)

    print("email [" +str(email) + "] password [" + str(password) + "]")

    s30api = s30api_async.s30api_async(email, password)

    if await s30api.serverConnect() == False:
        print("Connection Failed")
        return False

    for lsystem in s30api.getSystems():
        if await s30api.subscribe(lsystem) == False:
            print("Data Subscription Failed lsystem [" + str(lsystem) + "]")
            return False
    count = 0
    while (count == 0):
        await s30api.retrieve()
        for lsystem in s30api.getSystems():
                for zone in lsystem.getZoneList():
                    count += 1
        await asyncio.sleep(1)

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

