#!/bin/sh

. /etc/tejo.conf

pkill -f refresh_workload_list.py
/bin/tcsh -c 'python ${home_dir}/tejo/common/experiments_scripts/peers/refresh_workload_list.py  >& /tmp/refresh_workload.log'