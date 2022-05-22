# Lennox S30 Sibling Configuration

Sibling Configuration occurs when there is more than one S30 controller on your network. Typically, each S30 is running it's own furnace / heatpump. And, the thermostat panels allow you to control the zones on either S30.

When in this mode messages are routed between the S30s. If you have received the warning message "processMessage dropping message from sibling [{sysId}] for system [{system.sysId}]", this means the integration has received a message the propogated from one S30 to the other and then to the integration and has dropped the message. There is no harm in the message being dropped. However, this does mean increased network load and increased load on the S30 and your connection to Lennox Cloud.

This condition does not alway occur and we are still trying to determine when / why this happens, so if it does please open an issue. Possible causes of this condition:

- Using the same application_id on both integrations. You may want to change one of the integrations configuration from the default **homeassistant** to **ha_1** or some other unique string.
- Having diagnostics enabled

Or perhaps, using the thermostats to control the other zones.

As we find more information we will keep this topic up to date.
