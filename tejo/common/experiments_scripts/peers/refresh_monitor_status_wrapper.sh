#!/bin/sh

. /etc/tejo.conf

pkill -f refresh_monitor_status.py
/bin/tcsh -c "python ${home_dir}/tejo/common/experiments_scripts/peers/refresh_monitor_status.py  >& /tmp/refresh_monitor_status.log"

python -c "import pickle ; print pickle.load( open( '$workload_monitors_status_file', 'rb' ) )"
if [ $? -eq 0 ]
then
	sudo cp $workload_monitors_status_file $www_dir
else
	rm $workload_monitors_status_file
fi


exit 0