#!/bin/sh

. /etc/svc.conf
. ${home_dir}/svc/experiments_scripts/db/volt/config

echo -n copying:

for vm in `echo $vms|sed -r 's/[,]+/ /g'`
do
        if [ $vm != $volt_leader ]
        then
                ssh -o StrictHostKeyChecking=no $vm $COPY_DEP_FILE
        fi
done
echo done.
exit 0

