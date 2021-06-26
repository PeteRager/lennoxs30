# Lennox iComfort Component
A custom component for Home Assistant to integrate with Lennox iComfort S30 or Lennox iComfort E30 thermostats

> **Please Note:** This component **does not** support the other models of Lennox Thermostats 

# Requirements

- Home Assistant >= 2021.04.06  (others may work)
- Thermostat linked to a lennoxicomfort.com account

# Installation

1.  Go to releases in this repo and downloss the latest zip or clone the repo
2.  If upgrading from a prior release, pleast remove ALL files from the &lt;HA config directory&gt;/custom_components/lennoxs30 folder.
3.  Copy the 'lennoxs30' folder and contents to &lt;HA config directory&gt;/custom_components/ 
4.  Add the configuration to configuration.yaml.  If HA is running and you press the "Validate Configuration" button you may get an error.  HA must be restarted before it will see the new custom component.
5.  Restart HA


# Configuration
Configuration of the integration is done in configuration.yaml

## Minimal

```yaml
lennoxs30:
   email: myemail@myemail.com
   password: mypassword
```

## All options a debug turned on

```yaml
lennoxs30:
   email: myemail@myemail.com
   password: mypassword
   scan_interval: 30
   fast_scan_interval: 0.5

# Enable logging if reporting issues  
logger:
  default: info
  logs:
    custom_components.lennoxs30: debug
    custom_components.lennoxs30.climate: debug
    lennoxs30api: debug    
```


### Configuration Parameters
| Name | Type | Requirement | Default | Description |
| ---- | ---- | ----------- | ------- | ----------- |
| email | string | required | none | Cloud service account username |
| password | string | required | none | Cloud service account password |
| scan_interval| int | optional | 15 | Scan interval to check for cloud messages in seconds|
| fast_scan_interval| float | optional | 0.75 | After issuing a command (setpoint change, hvac mode change, etc.) The system goes into a fast scan mode, in order to make the UI more responsive to commands|

# Entities
## Climate

This integration will automatically detect all the homes, systems and zones in your account and add a Climate Entity for each discovered zone.  The names of the climate entities will be

*climate.<system_name>_<zone_name>*


System name is the name you gave to your S30.  By default Lennox names the Zones - "Zone 1", "Zone 2", "Zone 3", "Zone 4"

The integration creates internal Entity_Ids using the GUID of your S30 plus the zone index (0,1,2,3).

### Supported operations

**HVAC_MODE** supports **off**, **cool**, **heat** or **heat_cool** mode.  The speficic modes available depend on you equipemnt. For example an AC does not support heat, hence the heat and heat_cool modes would not appear in HA.

**FAN_MODE**  may be set to **auto**, **on**, **circulate**.

**Heating** and **cooling** setpoints can be set

**Presets** are supported.  The Preset List is the list of schedules that you have configured in the S30.  

When you are running a schedule; changes to the temperature or fan create a temporary schedule override (the Mobile APP does the same thing).  The override will automatically end at the end of the Next Period (e.g. at the time of your next schedule period.)  To cancel the override, there is a preset called "Cancel Hold".  Invoking this preset will remove the hold and re-enable the underlying schedule.

### Supported Data

The integration provides all of the standard climate attributes, including
1. Temperature
2. Humidity
3. Current HVAC action
4. Active setpoints
5. Active Preset

In additon the following extra attributes are provided, to allow for a more detailed information on the current zone operation.

| Attribute Name | Description | 
| ---- | ---- |
| fan | Indicates if the fan is currently running |
| damper | Position of damper - range 0-100 |
| tempOperation | Current acvtive temperatue operation heating or cooling |
| humidityOperation | Current active humidty operation - Drying or humidfying |
| allergenDefender | Indicates if this is enabled on the zone |

## lennoxs30.state

The entity is automatically created in Home Assistant and can be used to track the state and health of the connection to the cloud.

| State | Description |
| ----- | ----------- |
| Connected | API is connected to cloud system.  This is the desired state|
| Connecting | API is trying to connect to the cloud system.|
| Disconnected | API has failed to connect to cloud and will not try again.  Please raise an issue if you encounter this state|
| Login Failed | The login failued due to bad email/password combination.  Please correct credentials and restart HA|
| Waiting to Retry | The API was unable to connect or lost connection and is waiting to attempt a retry|
| Failed | The API failed.  Please raise an issue if you encounter this state |

The entity also has a set of attributes to provide diagnostic data:

| Attribute | Type |Description |
| --------- | ---- | ---------- |
| message_count|int| number of messages received from Lennox Cloud |
| send_count|int| number of messages sent to Lennox Cloud|
| receive_count|int| number of queries to recieve new messages.  Most queries return no messages|
| bytes_in| int | number of byte received|
| bytes_out| int | number of bytes sent|
| error_count| int | number of errors|
| http_2xx | int | number of HTTP responses received between 200-299. THese are good responses|
| http_4xx | int | number of HTTP responses received between 400-499. These usually indicate a problem with authorization|
| http_5xx | int | number of HTTP responses received between 500-599. These indicate a problem with the Lennox Cloud Servers.  Seeing a few of these a day is normal|
|last_receive_time| DateTime| Time of last succesful receive.  Should not be more than SCAN_INTERVAL seconds plus few seconds plus the metric update interval (90 seconds).  In other words is this time is more than 5 minutes ago using default SCAN_INTERVAL something is wrong.|
|last_error_time| DateTime| Time of the last error response|
|last_reconnect_time| DateTime| Time of the last reconnect or the time of the initial connect|
|last_message_time| DateTime| Time of the last message from Lennox Cloud.  How often messages are received is based on how often data is changing in the thermostat.  For example, a temperature change, a setpoint change will cause a message to be sent. If nothing is changing nothing will be sent|

##  sensor for Outdoor Temperature
Lennox systems may have an outdoor temperature sensor.  If your system has one a sensor will be automatically created.  It's name will be

sensor.<system_name>_outdoor_temperature

# Reporting Bugs

Please create issues to track bugs.  Please capture the logs with debug turned on.

## A note on Debug Log Files

The Lennox configuration that comes back from the API contains every configuration parameter of your system - including Personally Identifiable Information.  It is highly recommend to not publicly post these log files.  Information includes - the address of your residence and email address.  Issues #14 tracks this and we will work to scrub this information from the log file.  If I need a logfile or troubleshooting I will ask you to email it  

# Enhancement Requests

Enhancement requests are welcomed and encouraged.  Please log issues for us to track enhancements.



