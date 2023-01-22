# Samples Diag_Level

## Purpose

When the Lennox Controller reboots (for example after a power failure) the diag level resets to zero. The purpose of this sample is to provide an automation to detect the diag level being reset to zero and to return it to level 2.

## Components

The package contains an input_boolean that is used to enable / disable the automation. You should turn this on if you want the automation to automatically return it to level 2. Turn it off if a Lennox service guy is coming.

The package contains an automation that detects the level being at 0 for 1 minute, after which it sets it to level 2.

## Build Process

Edit the YAML files manually and replace SYSTEM_NAME with your lennox system name and copy these into home assitant. Or, edit the build.sh file and set the TARGET_PATH to the desination directory and SYSTEM_NAME to your lennox system name, then run ./build.sh froma linux command prompt.
