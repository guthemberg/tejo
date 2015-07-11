#!/bin/sh

LOG_FILE=/var/log/voltdb_run.log

if pgrep -f voltdb >/dev/null 2>&1; then sudo pkill -f voltdb; fi

sudo rm -rf /var/lib/voltdb/*; sudo mkdir /var/lib/voltdb/vroot; sudo mkdir /var/lib/voltdb/archive; sudo chown -R voltdb:voltdb /var/lib/voltdb;

if [ ! -e "$LOG_FILE" ]; then
	sudo touch $LOG_FILE;
	sudo chown voltdb:voltdb $LOG_FILE;
fi
 	
