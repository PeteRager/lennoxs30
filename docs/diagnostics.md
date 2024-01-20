# Lennox S30 Diagnostic Configuration

## Updates 2024-01

**WARNING** improperly configuring diagnostics may cause system stability issues - including excessive controller reboots. communication instability and loss of control. As of Jan 2024, Lennox firmware updates have improved the stability (or at least we are receiving less reports of issues)

In order to use diagnostics, your network should be setup to prevent the S30 from communicating to the Lennox Cloud. This will require router and firewall configuration. When diagnostics is enabled the data updates every 4 seconds and will be sent to the integration and the Lennox Cloud.

If you are using the integration for the first time, the recommendation is to get your system working without diagnostics for a week, to prove it is stable.

The purpose of this page is to:

- Describe what diagnostics are and how they work
- Provide system configuration guidance on how to setup diagnostics.
- Reference Architecture

## What are diagnostics?

Diagnostics provide access to HVAC data (currents, voltages, fan speeds, temperatures, etc.) Typically, a technician using a tablet will use this data when commissioning or servicing your system. The technician does this by pressing a button on the S30, which causes it to disconnect from your wifi and enable its own temporary WIFI network which the technician uses to access the system.

The diagnostic data you'll get is specific to the equipment that is installed. 40-50 sensors is typical.

For us Home Assistant enthusiasts, this primary use case is real-time power consumption.

## How does it work and not work?

Enabling diagnostic is done by setting the system diagnostic level from its default 0 to 2. When enabled, the system sends an update every 4 seconds containing the sensor data. This is sent to every connected client, which includes this integration, the lennox cloud and the Lennox App on your phone. This is where the problems occur. We believe when there is not be enough bandwidth to push the diagnostic data to the Lennox Cloud, across fhe cellular network to the phone apps. This causes data to start backing up in the S30 and eventually it exceeds a limit (runs out of memory?) and reboots. When it is rebooting your HVAC is off. Once it comes back up, the cycle repeats.

Note:  As of December 2023 on S40s that are internet connected, it appears that Lennox is automatically disabling diagnostics after a timeout. This is likely to prevent excessive data hitting their cloud. This behavior has not been reported on S40s that are not internet connected. While the **official** recommendation is to not operate diagnsotics with a cloud connected system. If you are cloud connected and see this behavior the following script has been shown to automatically correct the issue.

```
alias: Fix Lennox S40 Diagnostics
description: ""
trigger:
  - platform: time_pattern
    minutes: "0"
  - platform: time_pattern
    minutes: "15"
  - platform: time_pattern
    minutes: "30"
  - platform: time_pattern
    minutes: "45"
condition: []
action:
  - service: number.set_value
    data:
      value: "1"
    target:
      entity_id: number.lennox_diagnostic_level
    enabled: true
  - service: number.set_value
    data:
      value: "2"
    target:
      entity_id: number.lennox_diagnostic_level
mode: single
```

It is certainly possible that it can be stable with an internet connected phone app. All we do know, is many stability issues have occurred when enabling diagnostic with internet connected S30s. And the only known stable systems are internet isolated.

## Blocking the internet

There are two items that should be setup.

1.  Block DNS
2.  Block outgoing on all ports, all protocols - Lennox uses both TCP and UDP outgoing
3.  Allow access to an NTP time server to keep the S30 clock synced (recommended may not be required?)

Once that is configured, you'll need to restart the router or the S30, as firewalls do not block already established connections.

There are two binary sensors in Home Assistant that indicate the "Internet" and "Relay Server" connection status. Those should go to **disconnected** when the configuration is successful. Note: The S30 checks these connections periodically - so it may take a while for them to update. To accelerate the checking, go to the S30 panel, select Settings and click on WIFI - this should cause it to immediately check and update these sensors.

## Reference Architecture

### Separate IOT Wifi Network

The S30 is running your HVAC system which is critical infrastructure. To prevent malicious attacks you want to have this isolated and protected. I had an old wifi router laying around, put the S30 on it.

### Firewall

This function may be in your router. I use a PFSense firewall appliance between the IOT network and the main Wifi network. I have two sets of rules:

- Block internet - this is where I block all outgoing.
- Allow access to port 443 - this is where I allow incoming connections from Home Assistant and my development computer to connect to the S30.
