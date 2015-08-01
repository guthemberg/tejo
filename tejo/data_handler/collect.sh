#!/bin/sh

. /etc/tejo.conf

MAX_TIME=60 #seconds
collect_time=`grep collect_delay /etc/tejo.conf | cut -d= -f2`
home_dir=`grep home_dir /etc/tejo.conf | cut -d= -f2`
intervals=`echo "($MAX_TIME / $collect_time)"|bc`

echo "$intervals"

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

if [ "$db_tunnelling" = "yes" -o "$db_tunnelling" = "Yes"  -o "$db_tunnelling" = "Y"  -o "$db_tunnelling" = "y"  -o "$db_tunnelling" = "True"  -o "$db_tunnelling" = "true" ]; then
	close_ssh_tunnel_to_db
	open_ssh_tunnel_to_db
fi

i=0

while :;
do
	start=`date +"%s"`
        /bin/tcsh -c "python ${home_dir}/tejo/data_handler/save_vm_slo_measurements.py"
        now=`date +"%s"`
        passed=`expr $now - $start`
	remaining=`expr $collect_time - $passed`
	i=`echo "$i + 1"|bc`
	if [ $i -eq $intervals ]; then
		break
	else
		echo "sleeping $remaining"
		sleep $remaining
	fi
done 

if [ "$db_tunnelling" = "yes" -o "$db_tunnelling" = "Yes"  -o "$db_tunnelling" = "Y"  -o "$db_tunnelling" = "y"  -o "$db_tunnelling" = "True"  -o "$db_tunnelling" = "true" ]; then
	close_ssh_tunnel_to_db
fi
