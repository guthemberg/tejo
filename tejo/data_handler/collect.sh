#!/bin/sh

MAX_TIME=60 #seconds
collect_time=`grep collect_delay /etc/tejo.conf | cut -d= -f2`
home_dir=`grep home_dir /etc/tejo.conf | cut -d= -f2`
intervals=`echo "($MAX_TIME / $collect_time)"|bc`

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
		sleep $remaining
	fi
done 

