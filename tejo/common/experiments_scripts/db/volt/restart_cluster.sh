#!/bin/sh

. /etc/svc.conf
. /home/user/svc/svc/experiments_scripts/db/volt/config

SYSTEM_ID=0
GOOD=1
if [ $# -eq 1 ]; then
        if [ $1 -ne 1 -a $1 -ne 3 ]; then
                GOOD=0
        else
                SYSTEM_ID=$1
        fi
else
	GOOD=0
fi

if [ $GOOD -ne 1 ]; then
        echo "invalid parameters, please try restart_cluster.sh {1,3}"
        exit 1
fi

sh ${home_dir}/svc/experiments_scripts/db/volt/stop_cluster.sh

sh ${home_dir}/svc/experiments_scripts/db/volt/copy_dep_file_cluster.sh

sleep 1


sh ${home_dir}/svc/experiments_scripts/db/volt/start_cluster.sh $SYSTEM_ID

exit 0