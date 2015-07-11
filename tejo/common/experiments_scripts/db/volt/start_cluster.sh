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
        echo "invalid parameters, please try start_cluster.sh {1,3}"
        exit 1
fi

echo -n "starting(and tail logs):"

for vm in `echo $vms|sed -r 's/[,]+/ /g'`
do
        ssh -o StrictHostKeyChecking=no $vm $START_VOLTDB $SYSTEM_ID
done

echo "startup waiting time of 20 sec."

sleep 20

ssh $volt_leader tail -n 10 /var/log/voltdb_run.log

echo done.

exit 0