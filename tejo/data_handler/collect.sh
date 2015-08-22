#!/bin/sh

. /etc/tejo.conf

MAX_TIME=60 #seconds
collect_time=`grep collect_delay /etc/tejo.conf | cut -d= -f2`
home_dir=`grep home_dir /etc/tejo.conf | cut -d= -f2`
intervals=`echo "($MAX_TIME / $collect_time)"|bc`

close_ssh_tunnel_to_db () 
{
	pkill -f ${guest_vm_sys_user}@${db_master}
}

open_ssh_tunnel_to_db ()
{
	ssh -i ${root_dir}/.ssh/id_rsa_cloud -o StrictHostKeyChecking=no -f ${guest_vm_sys_user}@${db_master} -L ${db_port}:${db_host}:5432 -N	
}

#main
/usr/bin/pkill -f save_vm_slo_measurements.py

if [ "$db_tunnelling" = "yes" -o "$db_tunnelling" = "Yes"  -o "$db_tunnelling" = "Y"  -o "$db_tunnelling" = "y"  -o "$db_tunnelling" = "True"  -o "$db_tunnelling" = "true"   -o "$db_tunnelling" = "1"   -o "$db_tunnelling" = "t"   -o "$db_tunnelling" = "yeah" ]; then
	if [ `pgrep -f ${guest_vm_sys_user}@${db_master}|wc -l` -lt 1 ]
	then
		close_ssh_tunnel_to_db
		open_ssh_tunnel_to_db
	fi
fi

i=0

status=0
max_delta=0
resto=$MAX_TIME
seconds=0
while :;
do
	start=`date +"%s"`
        /bin/tcsh -c "python ${home_dir}/tejo/data_handler/save_vm_slo_measurements.py $seconds"
        seconds=`expr $seconds + $collect_time`
        status=$?
        now=`date +"%s"`
        passed=`expr $now - $start`
    if [ $resto -gt $passed ]
    then
    	resto=`expr $resto - $passed`
    else
    	resto=0
    fi
    if [ $passed -gt $max_delta ]
    then
    	max_delta=$passed
    fi
    if [ $passed -lt $collect_time ]
    then
		remaining=`expr $collect_time - $passed`
    else
    	remaining=1
    fi
	i=`echo "$i + 1"|bc`
	if [ $i -eq $intervals -o $max_delta -gt $resto ]; then
		break
	else
		echo "sleeping $remaining"
		sleep $remaining
	fi
done 

if [ "$db_tunnelling" = "yes" -o "$db_tunnelling" = "Yes"  -o "$db_tunnelling" = "Y"  -o "$db_tunnelling" = "y"  -o "$db_tunnelling" = "True"  -o "$db_tunnelling" = "true" ]; then
	if [ $status -gt 0 ]
	then
		close_ssh_tunnel_to_db
	fi
fi
