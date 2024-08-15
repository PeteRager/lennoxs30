# Aux Heat

## Overview

Home Assistant has deprecated aux_heat and will remove it from the product in 2024.10.0

This integration will continue to support aux heat until 2024.8.0

If you are using aux heat you will need to migrate to use the new functionality before that date.

## Changes

A new select entity is created for each zone for systems that have aux heat. The name of the entity is **select.[system_name]_[zone_name]_hvac_mode()**

This select entity will have all the valid hvac_modes for your system including **emergency heat**. You can select emergency heat directly from the drop down or use the service call:

```yaml
service: select.select_option
target:
  entity_id: select.ragehouse_zone_1_hvac_mode
data:
  option: "emergency heat"
```

The climate entity hvac_mode will be heat when the lennox hvac_mode is heat or emergency heat. Changing the hvac_mode in the climate entity will cause the select to update.
