#!/bin/bash

# This script is intended to list all the subtle details that have to be taken
# care of when setting up the DLNA server. The intention is that this script
# can be used to automate the setup. However, it was not tested so far, so it
# should be used with care.

scriptdir=/opt/DLNA
sudo mkdir -p "$scriptdir"

# Create and populate new groups. These are needed to restrict the write access
# to music files as far as possible.
user=$USER
newgroup=dlnausers
sudo groupadd $newgroup
sudo addgroup $user minidlna $newgroup

# Add configuration lines to corresponding files
echo "00 4  * * * root  /opt/DLNA/dlna_einrichten.sh" | sudo tee -a /etc/crontab
echo "extraargs=acpi=off" | sudo tee -a /boot/armbianEnv.txt
echo 'UUID="e69f73d8-44f3-4cf9-b965-c6a35fde05e5" /media/Daten ext4 defaults,nofail 0 2' | sudo tee -a /etc/fstab
