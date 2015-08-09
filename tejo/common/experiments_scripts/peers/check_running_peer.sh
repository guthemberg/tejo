#!/bin/sh

. /etc/tejo.conf

patern="ycsb-0.1.4"


if [ $system_id -eq 0 ]
then
	patern="ycsb-0.1.4"
fi

if [ -e $mongo_active_wl_file -a `pgrep -f $patern|wc -l` -eq 0 ]
then
	if [ `pgrep -f gmond|wc -l` -ge 1 ]
	then
		echo ok
	else
		echo failled
	fi
else
	echo failled
fi

