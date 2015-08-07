#!/bin/sh

. /etc/tejo.conf

if [ -e $mongo_active_wl_file -a `pgrep -f ycsb-0.1.4|wc -l` -eq 0 ]
then
	sh ${home_dir}/tejo/common/experiments_scripts/ycsb/run.sh $system_id $mongo_default_throughput &
fi