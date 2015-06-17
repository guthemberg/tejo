#!/bin/sh

. /etc/tejo.conf
. /home/user/tejo/tejo/experiments_scripts/db/volt/config

anything=$1

echo -n "run $anything all VMs:"

for vm in `echo $vms|sed -r 's/[,]+/ /g'`
do
        ssh -o StrictHostKeyChecking=no $vm $anything
done

echo done.

exit