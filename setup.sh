#!/bin/bash

# This script is intended to list all the subtle details that have to be taken
# care of when setting up the DLNA server. The intention is that this script
# can be used to automate the setup. Albeit it was tested successfully, it
# should be used with care.

if ! sudo -v
then
  echo Root privileges are required! >&2
  exit 1
fi

sudo aptitude install minidlna

scriptdir=/opt/DLNA
mountdir=/media/Daten
sudo mkdir -p "$scriptdir" "$mountdir"

# TODO Move files to $scriptdir.

global_conf=/etc/minidlna.conf
sudo rm "$global_conf"
sudo ln -s "$scriptdir/minidlna.conf" "$global_conf"

# Create and populate a new group `dlnausers'. This group is needed to restrict
# the write access to music files as far as possible. Assuming an existing HDD
# with data, everything should be setup correctly. How to configure the HDD is
# not part of this documentation and thus currently not documented.
newgroup=dlnausers
sudo groupadd $newgroup
sudo adduser $USER $newgroup
sudo adduser minidlna $newgroup

# Add configuration lines to corresponding files
echo "00 4  * * * minidlna /opt/DLNA/dlna_einrichten.sh" | sudo tee -a /etc/crontab
echo 'UUID="e69f73d8-44f3-4cf9-b965-c6a35fde05e5"' "$mountdir" 'ext4 defaults,nofail 0 2' | sudo tee -a /etc/fstab

sudo mount "$mountdir"

systemctl reboot
