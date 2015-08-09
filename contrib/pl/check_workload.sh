#!/bin/sh

. /etc/tejo.conf


patern="ycsb-0.1.4"


if [ $system_id -eq 0 ]
then
	patern="ycsb-0.1.4"
fi


if [ -e $mongo_active_wl_file ]
then
	if [ `pgrep -f $patern|wc -l` -eq 0 ] 
	then
		sh ${home_dir}/tejo/common/experiments_scripts/ycsb/run.sh $system_id $mongo_default_throughput &
	fi
fi