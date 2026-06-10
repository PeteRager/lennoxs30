"""Tests for zone runtime binary sensors."""

from unittest.mock import patch

import pytest

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from lennoxs30api.s30api_async import lennox_system, lennox_zone
from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.binary_sensor import (
    S30ZoneAllergenDefenderActiveBinarySensor,
    S30ZoneAuxiliaryHeatBinarySensor,
    S30ZoneDefrostBinarySensor,
    S30ZoneFanRunningBinarySensor,
)
from custom_components.lennoxs30.const import (
    LENNOX_DOMAIN,
    UNIQUE_ID_SUFFIX_ZONE_ALLERGEN_DEFENDER_ACTIVE,
    UNIQUE_ID_SUFFIX_ZONE_AUXILIARY_HEAT,
    UNIQUE_ID_SUFFIX_ZONE_DEFROST,
    UNIQUE_ID_SUFFIX_ZONE_FAN_RUNNING,
)
from tests.conftest import conftest_base_entity_availability


@pytest.mark.asyncio
async def test_zone_runtime_binary_sensors_init(hass, manager: Manager):
    """Test zone runtime binary sensors."""
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.getZone(0)

    allergen = S30ZoneAllergenDefenderActiveBinarySensor(hass, manager, system, zone)
    fan = S30ZoneFanRunningBinarySensor(hass, manager, system, zone)
    aux = S30ZoneAuxiliaryHeatBinarySensor(hass, manager, system, zone)
    defrost = S30ZoneDefrostBinarySensor(hass, manager, system, zone)

    assert allergen.unique_id == (zone.unique_id + UNIQUE_ID_SUFFIX_ZONE_ALLERGEN_DEFENDER_ACTIVE).replace("-", "")
    assert fan.unique_id == (zone.unique_id + UNIQUE_ID_SUFFIX_ZONE_FAN_RUNNING).replace("-", "")
    assert aux.unique_id == (zone.unique_id + UNIQUE_ID_SUFFIX_ZONE_AUXILIARY_HEAT).replace("-", "")
    assert defrost.unique_id == (zone.unique_id + UNIQUE_ID_SUFFIX_ZONE_DEFROST).replace("-", "")

    assert allergen.entity_category == "diagnostic"
    assert fan.entity_category == "diagnostic"
    assert aux.entity_category == "diagnostic"
    assert defrost.entity_category == "diagnostic"
    assert fan.device_class == BinarySensorDeviceClass.RUNNING

    zone.allergenDefender = True
    zone.fan = "on"
    zone.aux = True
    zone.defrost = False
    assert allergen.is_on is True
    assert fan.is_on is True
    assert aux.is_on is True
    assert defrost.is_on is False

    zone.allergenDefender = None
    zone.fan = "unexpected"
    zone.aux = None
    zone.defrost = None
    assert allergen.is_on is None
    assert fan.is_on is None
    assert aux.is_on is None
    assert defrost.is_on is None

    identifiers = fan.device_info["identifiers"]
    for ids in identifiers:
        assert ids[0] == LENNOX_DOMAIN
        assert ids[1] == zone.unique_id


@pytest.mark.asyncio
async def test_zone_runtime_binary_sensors_subscription(hass, manager: Manager):
    """Test zone runtime sensor subscriptions."""
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.getZone(0)

    allergen = S30ZoneAllergenDefenderActiveBinarySensor(hass, manager, system, zone)
    await allergen.async_added_to_hass()
    with patch.object(allergen, "schedule_update_ha_state") as update_callback:
        zone.attr_updater({"allergenDefender": True}, "allergenDefender")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert allergen.is_on is True

    fan = S30ZoneFanRunningBinarySensor(hass, manager, system, zone)
    await fan.async_added_to_hass()
    with patch.object(fan, "schedule_update_ha_state") as update_callback:
        zone.attr_updater({"fan": "off"}, "fan")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert fan.is_on is False

    aux = S30ZoneAuxiliaryHeatBinarySensor(hass, manager, system, zone)
    await aux.async_added_to_hass()
    with patch.object(aux, "schedule_update_ha_state") as update_callback:
        zone.attr_updater({"aux": True}, "aux")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert aux.is_on is True

    defrost = S30ZoneDefrostBinarySensor(hass, manager, system, zone)
    await defrost.async_added_to_hass()
    with patch.object(defrost, "schedule_update_ha_state") as update_callback:
        zone.attr_updater({"defrost": True}, "defrost")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert defrost.is_on is True

    conftest_base_entity_availability(manager, system, allergen)
