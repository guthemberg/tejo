#!/bin/sh

. /etc/tejo.conf

pkill -f refresh_workload_list.py
/bin/tcsh -c "python ${home_dir}/tejo/common/experiments_scripts/peers/refresh_workload_list.py  >& /tmp/refresh_workload.log"
python -c "import pickle ; print pickle.load( open( $monitors_list_file, 'rb' ) )"
if [ $? -eq 0 ]
then
	sudo cp $monitors_list_file $www_dir
fi
