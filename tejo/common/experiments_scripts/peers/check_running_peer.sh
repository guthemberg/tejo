#!/bin/sh

. /etc/tejo.conf

patern="ycsb-0.1.4"


if [ $system_id -eq 0 ]
then
	patern="ycsb-0.1.4"
fi

if [ -e "$mongo_active_wl_file" ]
then
	if [ `pgrep -f $patern|wc -l` -ge 1 ]
	then
		if [ `pgrep -f gmond|wc -l` -ge 1 ]
		then
			echo ok
			exit 0
		fi	
	fi
fi
echo failled
exit 1

