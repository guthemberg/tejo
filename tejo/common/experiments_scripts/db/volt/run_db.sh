#!/bin/sh

#coordinator host; e.g. vm-003.svc.laas.fr
COORDINATOR=$1
LOG_FILE=/var/log/voltdb_run.log

SYSTEM_ID=0
GOOD=1
if [ $# -eq 2 ]; then
        if [ $2 -ne 1 -a $2 -ne 3 ]; then
                GOOD=0
        else
                SYSTEM_ID=$2
        fi
else
	GOOD=0
fi

if [ $GOOD -ne 1 ]; then
        echo "invalid parameters, please try run_db.sh coordinator_hostname {1,3}"
        exit 1
fi

if [ $SYSTEM_ID -eq 1 ]; then
	sudo su - voltdb -c "export VOLTDB_HEAPMAX=3840; cd /var/lib/voltdb; voltdb create /etc/voltdb/tpcc.jar --deployment=/etc/voltdb/deployment.xml --host=${COORDINATOR} >> $LOG_FILE 2>&1 &"
elif [ $SYSTEM_ID -eq 3 ]; then
	sudo su - voltdb -c "export VOLTDB_HEAPMAX=3840; cd /var/lib/voltdb; voltdb create /etc/voltdb/voter.jar --deployment=/etc/voltdb/deployment.xml --host=${COORDINATOR} >> $LOG_FILE 2>&1 &"
fi

exit 0