#!/bin/sh

. /etc/svc.conf
. /home/user/svc/svc/experiments_scripts/db/volt/config

echo -n stopping:

for vm in `echo $vms|sed -r 's/[,]+/ /g'`
do
        ssh -o StrictHostKeyChecking=no $vm $STOP_VOLTDB
done

echo done.
exit 0