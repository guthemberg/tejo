#!/bin/sh


. /etc/tejo.conf


#### main

latency_result="`python $home_dir/contrib/pl/check_latency.py`"

if [ $? -eq 0 ]
then
	echo "computing latency (parameters: [${latency_result}])."
else
	exit 1
fi

action='ok'
smaller_target_throughput=0
bigger_target_throughput=0
rtt=0
to_kill=0

index=1
for parameter in `printf "$latency_result"`
do
	case $index in
		1)
			action=$parameter
			;;
		2)
			smaller_target_throughput=$parameter
			;;
		3)
			bigger_target_throughput=$parameter
			;;
		4)
			rtt=$parameter
			;;
		5)
			to_kill=$parameter
			;;
			
	esac
	index=`expr $index + 1` 
done

erase_rtt_list_flag=0
peer_is_dead=0

if [ $to_kill -eq 1 ]
then
		erase_rtt_list_flag=1
		peer_is_dead=1
		/bin/sh ${home_dir}/tejo/common/experiments_scripts/ycsb/stop.sh
		python $home_dir/contrib/pl/check_latency.py $peer_is_dead $erase_rtt_list_flag $rtt
		exit 0
fi


if [ "$actions" = "increase" ]
then
	if [ $bigger_target_throughput -gt $workload_throughput ]
	then
		erase_rtt_list_flag=1
		if [ $system_id -eq 0 ] 
		then
			sudo sed -i "s|workload_throughput=${workload_throughput}|workload_throughput=${bigger_target_throughput}" /etc/tejo.conf
			/bin/sh ${home_dir}/tejo/common/experiments_scripts/ycsb/stop.sh
			touch $mongo_active_wl_file
		fi
		/bin/sh ${home_dir}/contrib/pl/check_workload.sh
	fi
		
				
elif [ "$action" = "decrease" ]
then
	if [ $smaller_target_throughput -lt $workload_throughput ]
	then
		erase_rtt_list_flag=1
		if [ $system_id -eq 0 ] 
		then
			sudo sed -i "s|workload_throughput=${workload_throughput}|workload_throughput=${smaller_target_throughput}" /etc/tejo.conf
			/bin/sh ${home_dir}/tejo/common/experiments_scripts/ycsb/stop.sh
			touch $mongo_active_wl_file
		fi
		/bin/sh ${home_dir}/contrib/pl/check_workload.sh
	else
		/bin/sh ${home_dir}/tejo/common/experiments_scripts/ycsb/stop.sh
		peer_is_dead=1
	fi
	
#else
	#action ok
fi

python $home_dir/contrib/pl/check_latency.py $peer_is_dead $erase_rtt_list_flag $rtt