import logging
from lennoxs30api.s30api_async import (
    lennox_system,
)
from custom_components.lennoxs30 import (
    Manager,
)
import pytest
from custom_components.lennoxs30.const import MANAGER


from unittest.mock import Mock

from custom_components.lennoxs30.button import (
    EquipmentParameterUpdateButton,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_async_button_setup_entry(hass, manager: Manager, caplog):
    system: lennox_system = manager.api._systemList[0]
    entry = manager._config_entry
    hass.data["lennoxs30"] = {}
    hass.data["lennoxs30"][entry.unique_id] = {MANAGER: manager}

    manager._create_equipment_parameters = False
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 0

    manager._create_equipment_parameters = True
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1

    button_list = async_add_entities.call_args[0][0]
    assert len(button_list) == 1
    assert isinstance(button_list[0], EquipmentParameterUpdateButton)
