"""Test the ambinet lockout binary sensor"""
# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring

from unittest.mock import patch
import pytest


from lennoxs30api.s30api_async import lennox_system
from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import (
    LENNOX_DOMAIN,
    UNIQUE_ID_SUFFIX_AUX_HI_AMBIENT_LOCKOUT,
)
from custom_components.lennoxs30.binary_sensor import S30AuxheatHighAmbientLockout
from tests.conftest import conftest_base_entity_availability


@pytest.mark.asyncio
async def test_auxheat_lockout_init(hass, manager: Manager):
    """Test the binary sensor"""
    system: lennox_system = manager.api.system_list[0]
    sensor = S30AuxheatHighAmbientLockout(hass, manager, system)
    assert sensor.unique_id == (system.unique_id + UNIQUE_ID_SUFFIX_AUX_HI_AMBIENT_LOCKOUT).replace("-", "")
    assert sensor.extra_state_attributes is None
    assert sensor.update() is True
    assert sensor.should_poll is False
    assert sensor.name == system.name + "_auxheat_hi_ambient_lockout"
    assert sensor.available is True
    system.aux_heat_high_ambient_lockout = False
    assert sensor.state == "off"
    assert sensor.is_on is False
    system.aux_heat_high_ambient_lockout = True
    assert sensor.state == "on"
    assert sensor.is_on is True

    identifiers = sensor.device_info["identifiers"]
    for ids in identifiers:
        assert ids[0] == LENNOX_DOMAIN
        assert ids[1] == system.unique_id


@pytest.mark.asyncio
async def test_hauxheat_lockout_subscription(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    sensor = S30AuxheatHighAmbientLockout(hass, manager, system)
    await sensor.async_added_to_hass()

    with patch.object(sensor, "schedule_update_ha_state") as update_callback:
        update_set = {
            "aux_heat_high_ambient_lockout": True,
        }
        system.attr_updater(update_set, "aux_heat_high_ambient_lockout", "aux_heat_high_ambient_lockout")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert sensor.is_on is True
        assert sensor.available is True

    with patch.object(sensor, "schedule_update_ha_state") as update_callback:
        update_set = {
            "aux_heat_high_ambient_lockout": False,
        }
        system.attr_updater(update_set, "aux_heat_high_ambient_lockout", "aux_heat_high_ambient_lockout")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert sensor.is_on is False
        assert sensor.available is True

    conftest_base_entity_availability(manager, system, sensor)
