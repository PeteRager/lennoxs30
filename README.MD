# Lennox iComfort Component
A custom component for Home Assistant to integrate with Lennox iComfort S30 or Lennox iComfort E30 thermostats

> **Please Note:** This component **does not** support the other models of Lennox Thermostats 

# Requirements

- Home Assistant >= 2021.04.06  (others may work)
- Thermostat linked to a lennoxicomfort.com account

# Current State and Suggested Usage

The 0.0.3 has been tested in a Single Home with 2 S30 Controllers (5 Zones Total) running a Heat / Cool system.  Standard operations seem to work.

The 0.0.3 release is hardened for failure.  The system should recover automatically from network failures, internet failues and session expiration.  Error may be logged to indicae this.  Please provide errors that are encountered.

Recommended Usage:  Ready for production.

# Installation
Copy the 'lennoxs30' folder and contents to &lt;HA config directory&gt;/custom_components/ 

Add the configuration to configuration.yaml.  If HA is running and you press the "Validate Configuration" button you may get an error.  HA must be restarted before it will see the new custom component.

Restart HA

# Configuration
### Example configuation

Use your login information.  Please enabled debug when reporting issues or providing suggestions on missing capability.

```yaml
lennoxs30:
   email: myemail@myemail.com
   password: mypassword
   scan_interval: 30
   fast_scan_interval: 0.5

logger:
  default: info
  logs:
    custom_components.lennoxs30.s30api_async: debug
    custom_components.lennoxs30: debug
    custom_components.lennoxs30.climate: debug
```
# Behavior

This integration will automatically detect all the homes, systems and zones in your account and add a Climate Entity for each discovered zone.  The names of the climate entities will be climate.<system_name>_<zone_name>.

System name is the name you gave to your S30.  By default Lennox names the Zones - "Zone 1", "Zone 2", "Zone 3", "Zone 4"

The integration creates internal Entity_Ids using the GUID of your S30 plus the zone index (0,1,2,3).  Hence renaming your zone or system in the S30 should not cause duplicates.

# Functions

The HVAC_MODE of each zone may be set to off, cool, heat or heat_cool.  The speficic modes enabled will be specific to your HVAC equipment.

The FAN_MODE may be set to auto, on, circulate

The heating and cooling setpoints can be set

Zone Temperature and Humidity are reported

Presets are supported.  The Preset List is the list of schedules that you have configured in the S30.  When you are running a schedule; changes to the temperature or fan create a temporary schedule override (the Mobile APP does the same thing).  The override will automatically end at the end of the Next Period (e.g. at the time of your next schedule period.)  To cancel the override, there is a preset called "Cancel Hold".  Invoking this preset will remove the hold and re-enable the underlying schedule.

# Reporting Bugs

Please create issues to track bugs.  Please capture the logs with debug turned on.

## A note on Debug Log Files

The Lennox configuration that comes back from the API contains every configuration parameter of your system - including Personally Identifiable Information.  It is highly recommend to not publicly post these log files.  Information includes - the address of your residence and email address.  Issues #14 tracks this and we will work to scrub this information from the log file.



### Platform Parameters
| Name | Type | Requirement | Default | Description |
| ---- | ---- | ----------- | ------- | ----------- |
| email | string | required | none | Cloud service account username |
| password | string | required | none | Cloud service account password |
| scan_interval| int | optional | 15 | The normal scan mode to check for cloud messages in seconds|
| fast_scan_interval| float | optional | 0.5 | After issuing a command (setpoint change, hvac mode change, etc.) The system
goes into a fast scan mode, in order to make the UI more responsive to commands.  After 10 iterations or on confirmation of the change, the system returns to normal scan mode|

# Notes


