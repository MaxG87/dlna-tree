#!/bin/bash

set -euo pipefail

LOGFILE=/home/mgoerner/error-detection.log


function main() {
    parse_cli_args "$@"
    while true
    do
        print_debug_information >>"$LOGFILE" 2>&1
        sync
        sleep 3m
    done
}


function parse_cli_args() {
    if [[ $# -eq 1 ]]
    then
        arg="$1";shift
        if [[ "$arg" == "--help" || "$arg" == "-h" ]]
        then
            print_usage
            exit
        fi
        LOGFILE="$arg"
    elif [[ $# -gt 1 ]]
    then
        echo "Please provide at most one argument!" >&2
        exit 1
    fi
}


function print_usage() {
    cat <<EOF
$0 [LOGFILE]
EOF
}

function print_debug_information() {
    echo
    date
    uptime
    dmesg -uT | tail
    ip addr show wlxd85d4c97e434
    iwlist wlxd85d4c97e434 scan | egrep ESSID
    hdparm -acdgkmurC /dev/sda
    free
}


main "$@"
