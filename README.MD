# Lennox iComfort Component
A custom component for Home Assistant to integrate with Lennox iComfort S30 or Lennox iComfort E30 thermostats

> **Please Note:** This component **does not** support the other models of Lennox Thermostats 

# Requirements

- Home Assistant >= 2021.05.01
- Thermostat linked to a lennoxicomfort.com account

# Installation
Copy the 'lennoxs30' folder and contents to &lt;HA config directory&gt;/custom_components/ 

# Configuration
### Example configuation
```yaml
lennoxs30:
   email: myemail@myemail.com
   password: mypassword
  
```
# Behavior

This integration will automatically detect all the  homes, systems and zones in your account and add a Climate Entity for each discovered zone.

# Functions

The HVAC_MODE of each zone may be set to off, cool, or heat.

The FAN_MODE may be set to auto, on, circulate

The heating and cooling setpoints can be set

Zone Temperature and Humidity are reported

# Unsupported

My system is a single zone air conditioner.  Hence, many capabilites are unsupported due to ability to test and ability to intercept the API calls for functions outside of my system.  Your help is needed.

### Platform Parameters
| Name | Type | Requirement | Default | Description |
| ---- | ---- | ----------- | ------- | ----------- |
| email | string | required | none | Cloud service account username |
| password | string | required | none | Cloud service account password |

# Notes


