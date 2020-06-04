#!/bin/bash

set -euo pipefail

# This script is intended to list all the subtle details that have to be taken
# care of when setting up the DLNA server. The intention is that this script
# can be used to automate the setup. Albeit it was tested successfully, it
# should be used with care.

# SETTING UP THE HDD
# It does not seem to be appropriate to script the setup of the HDD. However,
# it shall be documented briefly:
#
# 1. Ensure that there is a partition with a sane file system. Ext4 or BTRFS
#    will do.
# 2. Add the music, e.g. via `rsync -a --progress /path/to/music /path/to/mount/of/device/`.
#    It is important to ommit the '/' at the end of the first path. Note
#    further that currently the folder containing the music must be of name
#    'Musik'.
# 3. Adapt the entry to /etc/fstab by adding the appropriate UUID. The UUID can
#    be determined using `blkid`.
# 4. Double check the ownership and permissions on /media/Daten/ and
#    /media/Daten/Musik. There is a draft function to set these up, but its not
#    yet tested.


function create_necessary_directories() {
    sudo mkdir -p "$mountdir"
    sudo mkdir -p "$scriptdir"
}


function move_script_to_scriptdir() {
    sudo cp * "$scriptdir"
}


function setup_server() {
    sudo apt --assume-yes install minidlna

    sudo rm "$global_conf"
    sudo ln -s "$scriptdir/minidlna.conf" "$global_conf"

    # Create and populate a new group `dlnausers'. This group is needed to
    # restrict the write access to music files as far as possible. Assuming an
    # existing HDD with data, everything should be setup correctly.
    newgroup=dlnausers
    sudo groupadd $newgroup
    sudo adduser $USER $newgroup
    sudo adduser minidlna $newgroup

    # Add configuration lines to corresponding files
    echo "00 4  * * * root /opt/DLNA/dlna_einrichten.sh" | sudo tee -a /etc/crontab
    echo "UUID=\"$UUID\"" "$mountdir" 'btrfs defaults,nofail 0 2' | sudo tee -a /etc/fstab
}


function setup_file_permissions() {
    # THIS FUNCTION WAS NEVER RUN!
    sudo chown $USER:dlnausers -R "$mountdir"
    sudo chmod 775 "$mountdir"
}

function configure_hdd() {
    cat <<EOF | sudo tee -a /etc/hdparm.conf
/dev/disk/by-uuid/$UUID {
	spindown_time = 60
	write_cache = off
}
EOF
}


if ! sudo -v
then
    echo Root privileges are required! >&2
    exit 1
fi

global_conf=/etc/minidlna.conf
mountdir=/media/Daten # Do not change lighthearted. Unfortunately, this path is
                      # hardcoded in other scripts too!
dlnadir="$mountdir/DLNA"
musicdir="$mountdir/Musik"
scriptdir=/opt/DLNA
UUID=a9169522-d764-45d9-bf35-56dc25b5fd5f

create_necessary_directories
move_script_to_scriptdir
setup_server
setup_file_permissions
configure_hdd
sudo mount "$mountdir"
systemctl reboot
