#!/bin/sh

. /etc/tejo.conf

patern="ycsb-0.1.4"


if [ $system_id -eq 0 ]
then
	patern="ycsb-0.1.4"
fi

if [ `pgrep -f run.sh|wc -l` -ge 1 -o `pgrep -f $patern|wc -l` -ge 1 ]
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

