# Lennox S30/E30 Component

A custom component for Home Assistant to integrate with Lennox iComfort S30, E30 or M30 thermostats; supporting local LAN connections and Lennox
Cloud Connections depending on the device model. We believe these configurations work - let us know if your experience is different!

- S30 - cloud or local connections
- E30 - cloud or local connections
- M30 - cloud connections only.

> **Please Note:** This component **does not** support the other models of Lennox Thermostats.

# Requirements

- Home Assistant >= 2021.6.1 and tested on 2021.12.7
- S30/E30 Thermostat linked to a lennoxicomfort.com account or an S30/E30 Thermostat on local LAN with a static/ DHCP leased IP address

# Important Information

- If you are migrating from Cloud to Local connection. Please review the [cloud to local migration section](#Cloud-to-Local-Migration)
- If you are upgrading from 0.1.3 to this release. Please review the [upgrade migration section](#New-Releases)
- If you are migrating from a custom install to a HACS install. Please review the [HACS migration section](#Migrate-to-HACS-from-Manual-Installation)
- If you are running more than 1 Home Assistant communicating to the S30 (for example a test and prod system) - you _MUST_ use a different _app_id_ for each instance - [Detailed Configuration](#Detailed-Configuration-Parameters)
- The Power Inverter Diagnostic are in Alpha. Please review the [documentation](#Sensor-for-Inverter-Power) prior to using
- Passwords with special characters are not properly supported by the Lennox Cloud API and may not work. Known special characters that cause issues are & and ^. If your password contains these characters you may need to change it prior to using the integration.

# Installation

## HACS

HACS is recommended as it provides automated install and will notify you when updates are available.

This assumes you have [HACS](https://github.com/hacs/integration) installed and know how to use it. If you need help with this, go to the HACS project documentation.

Add custom repository in _HACS_

1. Click on HACS in your menu to open the HACS panel, then click on integrations (https://your.domain/hacs/integrations).
1. Click on the 3 dots in the top right corner.
1. Select "Custom repositories"
1. Add the URL to the repository: `https://github.com/PeteRager/lennoxs30`
1. Select the integration category.
1. Click the "ADD" button.

Add integration in _HACS_

1. In the HACS panel, go to integrations and click the '+ Explore & add repositories' button.
1. Search for `Lennox iComfort WiFi Thermostat Integration` and click `Install this repository in HACS`.
1. Restart HA to load the integration into HA.<br>
1. Follow the Configuration Instructions below

## Manually

1. Go to [releases](https://github.com/PeteRager/lennoxs30/releases) in this repo and download the latest zip or clone the repo
1. Extract the zip file and copy the `custom_components/lennoxs30` folder and all it's contents including the `translations` subfolder, into the `custom_components` folder in your HA installation. If upgrading from a prior release, please remove ALL files from this folder.
1. Restart HA.
1. Follow the Configuration Instructions below

# Configuration

Configuration of the integration is done within the Integrations Panel in Home Assistant.

1. Click on Configuration, then Integrations
1. Click _Add Integration_
1. Search for Lennox S30/E30

## Select Cloud or Local

The first step is to select a Cloud or a Local connection.

Most, will use the Local Connection. Local connections are faster and more reliable than Cloud Connections. To have this work requires that the S30 has a static IP address (DHCP lease), consult your router docunentation for how to configure this.

Why would you use a Cloud Connection? Perhaps you want to monitor your vacation home in the Alps? Or your parent's house?

Need both or have multiple S30s? You are able to run multiple local and multiple cloud connections at the same time. Each is configured using this process.

1. Select Cloud or Local (default) connection

## Local Configuration

The next step is providing the connection information.

1. Enter the IP address of the S30. Alternatively, you can use a DNS name. If you have firewalls and do port mapping you may specify the port (hostname:port or ip:port) By default the S30 exposes HTTPS on Port 443.
1. You can use the defaults for the rest of the fields, or adjust as needed. See detailed configuration parameters below. Configuration can be changed later when needed. See [Detailed Configuration](#Detailed-Configuration-Parameters)
1. Submit the form

At this point, the integration will attempt to connect to the S30 - this should take no more than 5-10 seconds. If it succeeds, the Advanced Configuration Page will appear. If it is unable to connect errors will be reported and detailed information will be in the Home Assistant log file. Go onto the Advanced Configuration section.

## Cloud Connection

If using a cloud connection. The next step is to specify the connection information.

1. Enter the email address associated with your Lennox iComfort account
1. Enter the password associated with your Lennox iComfort account
1. Use the defaults for the rest of the fields, or adjust as needed. See [Detailed Configuration](#Detailed-Configuration-Parameters)
1. Submit the form

At this point, the integration will attempt to connect to the S30 - this should take no more than 5-15 seconds. If it succeeds, the Advanced Configuration Page will appear. If it is unable to connect errors will be reported and detailed information will be in the Home Assistant log file. Go onto the Advanced Configuration section.

## Advanced Configuration

The next page brings up advanced configuration properties with the recommended defaults.

1. Use the defaults (recommended) or adjust using the [Detailed Configuration](#Detailed-Configuration-Parameters)
1. Press submit

At this point, the integration will connect to the S30, download and process its configuration (100kb) and create the Entities in Home Assistant. For local connections, this step typically takes 10-30 seconds complete, for cloud connections it an takes 15-45 seconds. If it is successful, you will be presented with a list of discovered devices. If it fails, review the error and look in the log file for more detailed information.

For Local Connections the Integration instance name is the ip_address / host name. For Cloud Connections the instance name is a redacted version of your email.

# Configuration Options

If you want to change the integration configuration, do into the integrations page, find the integration and click configure. This will bring up the set of options you can change. After saving, select Reload or Restart HA for the changes to take affect.

# Temperature Units (Celsius, Fahrenheit)

The integration detects the unit system configured in Home Assistant and reports the data in the correct units. Celsius is in 0.5 degree increments. Fahrenheit is in 1.0 degrees increments. The Lennox API delivers data in both units, so there is no conversion in the Integration and what you see in the Lennox UI should be what you see in HA.

# Devices

The integration will create a full set of devices representing your HVAC system. Note: depending on your HVAC configuration and the configuration options not all devices may have entities. Please don't delete the unused devices, they will be used as we add more entities in future releases

| Device Type  | Description                                                                                           | Name                           | Parent |
| ------------ | ----------------------------------------------------------------------------------------------------- | ------------------------------ | ------ |
| S30          | This is the HVAC controller, it is a little box with an antenna located near the indoor unit.         | S30 System Name                | None   |
| Indoor Unit  | This specifies the type of indoor unit you have. Examples, include `Furnace` and `Air Handler`.       | S30 System Name + Outdoor Unit | S30    |
| Outdoor Unit | This specifies the type of outdoor unit you have. Examples include `Heat Pump` and `Air Conditione`r. | S30 System Name + Indoor Unit  | S30    |
| Thermostat   | One thermostat device is created for each zone. These are mounted on the walls in your house.         | S30 System Name + Zone Name    | S30    |

# Entities

## Climate

_Cloud_ - Automatically detects all the zones across the homes and systems in your cloud account. Climate Entities created for each zone. The integration creates internal unique_ids using the Cloud GUID of your S30 plus the zone index (0,1,2,3).

_Local_ - Automatically detects all the zones in the S30 it is connected to. Climate Entities created for each zone. The integration creates internal unique_ids using the Serial Number of your S30 plus the zone index (0,1,2,3).

Entities are attached to the corresponding S30 Device and have default names (which you can change in Home Assistant)

_climate.<system*name>*<zone_name>_

System name is the name you gave to your S30. By default Lennox names the Zones - "Zone 1", "Zone 2", "Zone 3", "Zone 4" - this is configurable within the S30.

### Supported operations

**HVAC_MODE** supports **off**, **cool**, **heat** or **heat_cool** mode. The specific modes available depend on you equipment. For example an AC does not support heat, hence the heat and heat_cool modes will not be available.

**FAN_MODE** may be set to **auto**, **on**, **circulate**.

**Heating** and **cooling** setpoints can be set

**Presets** are supported. The Preset List is the list of schedules that you have configured in the S30.

When you are running a schedule; changes to the temperature or fan create a temporary schedule override (the Mobile APP does the same thing). The override will automatically end at the end of the Next Period (e.g. at the time of your next schedule period.) To cancel the override, there is a preset called **Cancel Hold**. Invoking this preset will remove the hold and re-enable the underlying schedule.

Away Mode. The **Away** preset will put the S30 system into Manual Away Mode. You could also use the manual away mode switch to do this. Works the same as if you pressed the away button on the S30 Panel

Cancel Manual Away Mode or Smart Away Mode. The **cancel away mode** preset will cancel the active away mode (manual or smart) and return the S30 system to whatever state it was in prior to putting it into away mode. This works the same as if you pressed the cancel away icon on the S30 panel.

**Emergency Heat** - Lennox systems that have a heat pump and an auxiliary furnace, have an additional HVAC_MODE to run just the auxiliary furnace. In the S30 App this is shown as Emergency Heat. Home Assistant **does not** allow this mode directly - instead Home Assistant provides support for turning aux_heat on and off - independent of the HVAC_MODE. The integration has the following behavior:

- If Emergency Heat Mode is set in the S30, the HA climate will show Heat and the Aux Heat switch will be on.
- If the HA Aux Switch is turned on, the S30 Heat Mode will be set to **Emergency Heat**
- If the HA Aux Switch is turned off, the S30 Heat Mode will be set to **Heat**
- If the Lennox Auxiliary Heat is running, the **aux** attribute in the HA Climate entity will be set to True and the HA Climate Entity will show **Heating**

### Supported Data

The integration provides all of the standard climate attributes, including

1. Temperature
2. Humidity
3. Current HVAC action
4. Active setpoints - dependent on the HVAC_MODE. For example, in Cool Mode the Cool Setpoint is shown, but not the Heat Setpoint.
5. Active Preset

In addition the following extra attributes are provided, to allow for a more detailed information on the current zone operation.

| Attribute Name    | Description                                                                                                                                                                                     |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| allergenDefender  | Indicates if this is enabled on the zone                                                                                                                                                        |
| aux               | Auxiliary Heating is On when True, off when False. Typically this means the hest pump is disabled and the furnace is running instead.                                                           |
| balancePoint      | This is related to heatpump lockout, details / values are not well known yet - if you know let us know!                                                                                         |
| coolCoast         | This will only appear in non-zoning systems and it indicates the system is set to a single setpoint mode, the system was in heating mode and has turned off to coast to the desired temperature |
| damper            | Position of damper - range 0-100. Observationally values are either 0 or 100; where 100 = damper open.                                                                                          |
| defrost           | Defrost is active                                                                                                                                                                               |
| demand            | CFM of air demand for the zone. Thanks @blyons16 for getting this information from his installers                                                                                               |
| fan               | Indicates if the fan is currently running. Note: this is true only when the fan is running and there is no active HVAC action (cooling, heating, etc.)                                          |
| heatCoast         | This will only appear in non-zoning systems and it indicates the system is set to a single setpoint mode, the system was in heating mode and has turned off to coast to the desired temperature |
| humidityOperation | Current active humidity operation - Drying or humidifying                                                                                                                                       |
| ssr               | Not known what this attribute indicates. If you know let us know!                                                                                                                               |
| tempOperation     | Current active temperature operation heating or cooling                                                                                                                                         |
| ventilation       | Indicates if external ventilation is currently active on this zone                                                                                                                              |

## lennoxs30.state or lennoxs30.conn\_\<hostname\> or lennoxs30.\_<redacted email_address\>

These entities is automatically created for each integration instance and can be used to track the state and health of the Cloud or Local connection to the S30. When using multiple LAN connections, the
first host in the list will use **lennoxs30.state** for backwards compatibility. Additional local connections will use a naming convention of **lennoxs30.conn\_<hostname>**. Cloud connections wil use lennoxs30.\_<redacted email_address\>

| State            | Description                                                                                               |
| ---------------- | --------------------------------------------------------------------------------------------------------- |
| Connected        | API is connected. This is the desired state                                                               |
| Connecting       | API is trying to connect                                                                                  |
| Disconnected     | API has failed to connect and will not try again. Please raise an issue if you encounter this state       |
| Login Failed     | The login failed due to bad email/password combination. Please correct credentials and reload integration |
| Waiting to Retry | The API was unable to connect or lost connection and is waiting to attempt a retry                        |
| Failed           | The API failed. Please raise an issue if you encounter this state                                         |

The entity also has a set of attributes to provide diagnostic data:

| Attribute           | Type     | Description                                                                                                                                                                                                                                                             |
| ------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| message_count       | int      | number of messages received from Lennox Cloud                                                                                                                                                                                                                           |
| send_count          | int      | number of messages sent                                                                                                                                                                                                                                                 |
| receive_count       | int      | number of queries to receive new messages. Most queries return no messages                                                                                                                                                                                              |
| bytes_in            | int      | number of bytes received                                                                                                                                                                                                                                                |
| bytes_out           | int      | number of bytes sent                                                                                                                                                                                                                                                    |
| error_count         | int      | number of errors                                                                                                                                                                                                                                                        |
| exceptions          | int      | number of network exceptions that have occurred                                                                                                                                                                                                                         |
| http_2xx            | int      | number of HTTP responses received between 200-299. These are good responses                                                                                                                                                                                             |
| http_4xx            | int      | number of HTTP responses received between 400-499. These usually indicate a problem with authorization                                                                                                                                                                  |
| http_5xx            | int      | number of HTTP responses received between 500-599. These indicate a problem with the Cloud or S30. Seeing a few of these a day is normal                                                                                                                                |
| last_receive_time   | DateTime | Time of last successful receive. Should not be more than SCAN_INTERVAL seconds plus few seconds plus the metric update interval (90 seconds). In other words is this time is more than 5 minutes ago using default SCAN_INTERVAL something is wrong.                    |
| last_error_time     | DateTime | Time of the last error response                                                                                                                                                                                                                                         |
| last_reconnect_time | DateTime | Time of the last reconnect or the time of the initial connect                                                                                                                                                                                                           |
| last_message_time   | DateTime | Time of the last message from Lennox Cloud. How often messages are received is based on how often data is changing in the thermostat. For example, a temperature change, a setpoint change will cause a message to be sent. If nothing is changing nothing will be sent |
| sysUpTime           | int      | Number of seconds the S30 has been running since last reboot. Note: for cloud connections this is updated once at startup. For local connections this updates every minute.                                                                                             |
| diagLevel           | int      | Current Diagnostic Level of the S30. By default this is zero, if using the power diagnostics this should be 1 or 2                                                                                                                                                      |
| softwareVersion     | string   | Current software version of the S30                                                                                                                                                                                                                                     |
| hostname            | string   | The hostname used by this connection or None if a cloud connection                                                                                                                                                                                                      |

## sensor for Zone Temperature and Humidity

When the **create_sensors** configuration parameter is set, humidity and temperature sensors are created for each zone. This is the default for new configurations. These sensors are attached to the Thermostat Device.

sensor.<system_name>\_<zone_name>\_temperature

sensor.<system_name>\_<zone_name>\_humidity

## sensor for Outdoor Temperature

Lennox systems may have an outdoor temperature sensor. If your system has one a sensor will be automatically created and attached to the Outdoor Unit Device. It's name will be

sensor.<system*name>\_outdoor_temperature - \_ALPHA*

## Sensor for Inverter Power

When the **create_inverter_power** configuration parameter is set, a power sensor entity will be created. Inverter Power can only be enabled for Local Connections. To get this information the S30 must be placed in Diagnostic Mode 2. To set the diagnostic mode see [diagnostic level](#diagnostic-level)

When diagnostics is enabled it should begin updating with the current power draw of the system. It's name will be

sensor.<system_name>\_inverter_energy

It can be combined with an Integration sensor to count the total energy usage over time, and this Integration sensor can be added to the Home Assistant Energy dashboard. A configuration similar to the following should work:

```yaml
sensor:
  - platform: integration
    source: sensor.<system_name>_inverter_energy
    name: <system_name>_inverter_kwh
    unit_prefix: k
    round: 2
```

This feature is in Alpha and we are looking for feedback and experiences using the data - and it's accuracy.

## switches

### allergen_defender

When the configuration parameter is true a switch will be created.

switch.<system_name>\_\_allergen_defender

The switch will reflect the current state of the allergen defender mode and will allow turning the mode on or off

### manual away mode

This switch reports the current state of manual away mode and allows turning manual away mode on or off.

switch.<system_name>\_manual_away_mode

### smart away enabled

This switch enables or disables smart away on the S30. This switch **does not** put the system into away mode. This switch enables the S30 to perform it's smart away detection of your mobile devices. To properly setup Smart Away you will need to use the Lennox Mobile App. Once smart away is setup, this allow you to turn the detection on or off.

switch.<system_name>\_manual_away_mode

### ventilation

If your system has an external outdoor air damper a switch will be created.

switch.<system_name>\_ventilation

The switch will reflect the current state of the ventilation damper and will allow turning the mode on or off.  
The switch has the following attributes:

| Attribute                | Type | Description                                                              |
| ------------------------ | ---- | ------------------------------------------------------------------------ |
| ventilationRemainingTime | int  | number of minutes remaining in ventilation action                        |
| ventilatingUntilTime     | int  | integer timestamp of the end time of the ventilation action              |
| diagVentilationRuntime   | int  | total number of minutes the system has ventilated for over it's lifetime |

## Binary Sensors

### home state

The home state binary sensor reports the current away mode of the S30. A value of 'on' indicates the system is in home mode. A value of 'off' indicates the system is in away mode. This sensor used the "presence" device class, so in Lovelace you will see the value of 'Home' or 'Away'.

binary_sensor.<system_name>\_home_state

The S30 has three setpoint states that are possible - Home, Transition and Away. For this binary sensor the Transition and Away states are reported as Away. The detailed information
is available within attributes of the binary sensor.

| Attribute                 | Type    | Description                                                                   |
| ------------------------- | ------- | ----------------------------------------------------------------------------- |
| manual_away               | boolean | True if manual away is turned on                                              |
| smart_away                | boolean | True if smart away has turned on away mode                                    |
| smart_away_enabled        | boolean | True is smart away is enabled                                                 |
| smart_away_state          | string  | State of smart away. See table below for values                               |
| smart_away_enabled        | boolean | True is smart away is enabled                                                 |
| smart_away_reset          | boolean | True if smart away has been reset, value may be transient                     |
| smart_away_cancel         | boolean | True if smart away has been cancelled, value may be transient                 |
| smart_away_setpoint_state | string  | Current setpoint state - "home", "transition", "away" are the observed values |

Smart Away State Values

| Value             | Type                                                                                                     |
| ----------------- | -------------------------------------------------------------------------------------------------------- |
| enabled cancelled | Indicates the system was in smart away and it was cancelled from either the app, panel or home assistant |
| enabled active    | Smart away detection is enabled, and smart away has determined you are away                              |
| enabled inactive  | Smart away detection is enabled, and smart away has determined you are home                              |
| disabled          | Smart away is disabled                                                                                   |

## Number

### diagnostic level

**ALPHA** When the power inverter option is enable, a Number entity is created to allow setting and reporting on the active diagnostic level in the S30. A value of zero indicates diagnostics is disabled. Values of 1 or 2 will cause the inverter power to be sent. Other values are invalid. The name of the entity is:

number.<system_name>\_diagnostic_level

Note: This capability in in _Alpha_ Mode. When enabled the S30 sends much more information. If you are using their IOS / Android App - this may impact the performance. It is not recommended to be toggling this mode frequently. Early on there were reports of the S30 rebooting that may have been caused by this - but it has not reproduced. If you are using this feature, you may want to monitor the lennoxS30.state sysuptime attribute. This value will reset to zero when the S30 reboots. The integration will log a warning if this is detected. Please report on your findings - we want to know if its working or not working for you!

# Reporting Bugs

Please create issues to track bugs. Please capture the logs with debug turned on.

Debug logging can be enabled by adding the following to your Home Assistant's configuration.yaml:

```yaml
logger:
  default: warning
  logs:
    custom_components.lennoxs30: debug
    lennoxs30api: debug
```

## A note on Debug Log Files

The Lennox configuration that comes back from the API contains every configuration parameter of your system - including Personally Identifiable Information. The system by default redacts this information in the log files. Still the recommendation is not to publicly post these. If we need them to debug an issue we can use email.

# Detailed Configuration Parameters

This section documents the detailed configuration parameters, that are editable through the UI. This configuration is stored in the config/.storage/core_config_entries file. Editing this file is not recommended.

| Name                     | Type    | Requirement | Default            | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ------------------------ | ------- | ----------- | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| scan_interval            | int     | optional    | 15                 | Scan interval to check for cloud messages in seconds. 15 seconds is recommended for cloud connections. For local connections this should not be set unless instructed                                                                                                                                                                                                                                                                                                                                                              |
| allergen_defender_switch | bool    | optional    | false              | When true creates a switch entity to allow control of allergenDefender mode                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| fast_scan_interval       | float   | optional    | 0.75               | After issuing a command (setpoint change, hvac mode change, etc.) The system goes into a fast scan mode, in order to make the UI more responsive to commands                                                                                                                                                                                                                                                                                                                                                                       |
| init_wait_time           | int     | optional    | 30                 | Amount of time to wait for configuration to arrive from Lennox during integration startup. Increase this value if you see initialization timeouts                                                                                                                                                                                                                                                                                                                                                                                  |
| app_id                   | string  | optional    | uniquely generated | Specify the unique application id to use. For Cloud connections, Lennox is very particular - please use this string - mapp0793723676444670468270xx - and replace xx with a value from 00 - 99. Note that each instance of your integration (e.g. prod system, test system) must use a different value for xx. For local connections use a string like ha_dev or ha_prod - must be unique for each connection                                                                                                                       |
| create_sensors           | bool    | optional    | false              | Creates temperature and humidity sensors for each zone                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| create_inverter_power    | bool    | optional    | false              | Creates a sensor representing the inverter power usage. This requires configuring the Lennox LCC diagnostic mode to be 1 or 2, as opposed to the default value of 0. Use the number.diagnostic_level entity to set this,.                                                                                                                                                                                                                                                                                                          |
| protocol                 | string  | optional    | https              | Selects the protocol to use. The only reason to use this is when developing using the S30 simulator, in which case this should be set to HTTP                                                                                                                                                                                                                                                                                                                                                                                      |
| message_debug_logging    | boolean | optional    | True               | When True messages are logged when debug is enabled. Setting to False omits the message from the debug log file.                                                                                                                                                                                                                                                                                                                                                                                                                   |
| log_messages_to_file     | string  | optional    |                    | When set all S30 messages for this connection will the logged to the specified file. If no path is specified, the file will appear on the home asssistant config directory - the same place the home_assistant.log file is. If you want the fie to be elsewhere specific a full path or relative path to the home assistant root directory. Messages will be logged regardless of debug settings. This provides an easy way to submit the message logs without having to submit all the stuff in the full home assistant log file. |
| pii_in_message_logs      | boolean | optional    | False              | When set to False personal information - email, passwords, street addresses, etc. are redacted from the log files. False is the default and the recommended setting for submitting logs. This parameter exists in the unlikely event this information is needed in troubleshooting.                                                                                                                                                                                                                                                |

# Migration

## New Releases

### Migration from 0.1.3 to 0.2.0

In Release 0.2.0 configuration is moved from configuration.yaml to the internal home assistant configuration repository. On startup of 0.2.0 (or later releases), the YAML configuration will be migrated to the repository. After HA starts please check your entities to verify they are working. Once verified remove the lennoxs30 configuration from configuration.yaml. All of your entities should be preserved and the migration should be seamless.

### Migration from <0.1.3 to 0.2.0

If you are on older versions of the integration. You may need to adjust your configuration in the YAML fie to meet the new requirements.

1. Start HA
2. Look for errors in the log indicating there is missing configuration
3. Add missing configuration
4. Restart

## Cloud to Local Migration

### Cloud to Local (have not upgraded to 0.2.0)

Use Case: You have the integration configured to use the cloud and you want to go local.
Current State: You are on 0.1.3

The simplest approach is to edit the configuration.yaml in 0.1.3 and add the ip_address in and restart HA.

When switching from Cloud to Local - new entities are created in Home Assistant. Perform the following steps after restarting:

- Go into the list of entities and delete the old entities (write down their names if needed)
- Rename the new entities using the old entity's entity ids.

### Cloud to Local (have upgraded to 0.2.0)

Use Case: You have the integration configured to use the cloud and you want to go local.
Current State: You are on 0.2.0 or greater.

- Go into Configuration / Integrations and Delete the cloud integration
- Add a new integration instance for the local connection.

## Migrate to HACS from Manual Installation

### Currently on 0.1.3

Perform the following steps:

1. Comment out the lennoxs30: section from configuration.yaml (use the #)
1. Moved the old custom_components/lennoxs30 directory to somewhere else so it wouldn't be found. Or delete it. Make sure the lennoxs30 directory no longer exists
1. Restart HA
1. Add custom repository in HACS per the [Instructions](#HACS)
1. Add integration in HACS per the instructions
1. Restart HA
1. Uncomment the lennoxs30: section from configuration.yaml
1. Restart HA

### Currently on 0.2.0

In 0.2.0 and greater the config for the integration is not stored in configuration.yaml.

Note: These steps are untested. Please provide feedback if this works :-).

Perform the following steps:

1. Moved the old custom_components/lennoxs30 directory to somewhere else so it wouldn't be found. Or delete it. Make sure the lennoxs30 directory no longer exists
1. Restart HA
1. Add custom repository in HACS per the [Instructions](#HACS)
1. Add integration in HACS per the instructions
1. Restart HA

At this point everything should just work.

# Network information

The local connection uses HTTPS to Port 443 outgoing to the S30.

The cloud connection using HTTPS to Port 443 outgoing to the Lennox Cloud.

There are no incoming connections.

# Enhancement Requests

Enhancement requests are welcomed and encouraged. Please log issues for us to track enhancements.

# Credits

This work is based in part great work done by these folks:

https://github.com/HyperActiveJ

https://github.com/hufman/lennox_lcc

https://github.com/thevoltagesource

# Donations

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/PeteRage)
