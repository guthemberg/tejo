#!/bin/sh


if [ `pgrep -f run.sh|wc -l` -ge 1 -o `pgrep -f ycsb-0.1.4|wc -l` -ge 1 ]
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

