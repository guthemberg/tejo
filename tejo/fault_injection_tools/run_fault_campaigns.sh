#!/bin/sh

. /etc/tejo.conf

#these parameters come from tejo.conf
#RECOVERY_DELAY=60
#FAULT_DURATION=300
#TRIES_PER_FAULT=2
#EXPERIMENT_ID=$1

get_random_vm_hostname()
{
	n_vms=`echo $vms|awk -F, '{print NF}'`
#the following command returns a random number (-p1) between 0 and 6 (-n5)
#host_index=`shuffle -n 6 -p1`
	random_index=`shuffle -n $n_vms -p1`
	random_vm_index=`expr $random_index + 1`
	echo $vms | cut -d, -f$random_vm_index
}

get_random_hostname()
{
	my_vms=$1
	n_my_vms=`echo $my_vms|awk -F, '{print NF}'`
	#the following command returns a random number (-p1) between 0 and 6 (-n5)
	#host_index=`shuffle -n 6 -p1`
	random_index=`shuffle -n $n_my_vms -p1`
	random_vm_index=`expr $random_index + 1`
	echo $my_vms | cut -d, -f$random_vm_index
}

remove_hostname()
{
	formated_list=`echo $1|sed -r 's/[,]+/ /g'`
	new_list=""
	for hostname in $formated_list
	do
	if [ $hostname != $2 ]; then
	        new_list="${hostname},${new_list}"
	fi
	done
	echo $new_list| rev | cut -c 2- | rev
}

pick_n_randomly()
{
        n=$1
        list=$2
        new_list=""
        while [ $n -gt 0 ]
        do
                hostname=`get_random_hostname $list`
                list=`remove_hostname $list $hostname`
                new_list="${hostname},$new_list"
                n=`expr $n - 1`
        done
        echo $new_list| rev | cut -c 2- | rev
}

##how to call
#inject target fault_type intensity
inject() {

	target=$1
	fault_type=$2
	intensity=$3
	system_id=$4
	
	while [ -e /tmp/pause_fc.txt ]
	do
		echo -n "It is paused for 60 second... "
		sleep 60
		echo "trying to resume now."
	done
	
	ts=`/bin/date`
	/bin/echo -n "[${ts}] injecting fault $fault_type with intensity of $intensity towards $target (fault dur. ${FAULT_DURATION} sec. in system $system_id)..."
	
	if [ $fault_type -eq 2 ]; then
	        ssh -o StrictHostKeyChecking=no $target "/bin/tcsh -c \"/bin/sh /home/user/tejo/tejo/fault_injection_tools/packet_loss_fault.sh $FAULT_DURATION $intensity $system_id >& /tmp/packet_loss_fault_${intensity}.log\""
	        /bin/sleep $RECOVERY_DELAY
	elif [ $fault_type -eq 3 ]; then
	        ssh -o StrictHostKeyChecking=no $target "/bin/tcsh -c \"/bin/sh /home/user/tejo/tejo/fault_injection_tools/latency_fault.sh $FAULT_DURATION $intensity $system_id >& /tmp/latency_fault_${intensity}.log\""
	        /bin/sleep $RECOVERY_DELAY
	elif [ $fault_type -eq 4 ]; then
	        ssh -o StrictHostKeyChecking=no $target "/bin/tcsh -c \"/bin/sh /home/user/tejo/tejo/fault_injection_tools/bandwidth_fault.sh $FAULT_DURATION $intensity $system_id >& /tmp/bandwidth_fault_${intensity}.log\""
	        /bin/sleep $RECOVERY_DELAY
	elif [ $fault_type -eq 5 ]; then
	        ssh -o StrictHostKeyChecking=no $target "/bin/tcsh -c \"/bin/sh /home/user/tejo/tejo/fault_injection_tools/memory_fault.sh $FAULT_DURATION $intensity $system_id >& /tmp/memory_fault_${intensity}.log\""
	        /bin/sleep $RECOVERY_DELAY
	        /bin/sleep $RECOVERY_DELAY
	        /bin/sleep $RECOVERY_DELAY
	        /bin/sleep $RECOVERY_DELAY
	        /bin/sleep $RECOVERY_DELAY
	elif [ $fault_type -eq 6 ]; then
	        ssh -o StrictHostKeyChecking=no $target "/bin/tcsh -c \"/bin/sh /home/user/tejo/tejo/fault_injection_tools/disk_fault.sh $FAULT_DURATION $intensity $system_id >& /tmp/disk_fault_${intensity}.log\""
	        /bin/sleep $RECOVERY_DELAY
	        /bin/sleep $RECOVERY_DELAY
	elif [ $fault_type -eq 7 ]; then
	        ssh -o StrictHostKeyChecking=no $target "/bin/tcsh -c \"/bin/sh /home/user/tejo/tejo/fault_injection_tools/cpu_fault.sh $FAULT_DURATION $intensity $system_id >& /tmp/cpu_fault_${intensity}.log\""
	        /bin/sleep $RECOVERY_DELAY
	        /bin/sleep $RECOVERY_DELAY
	else  
	        echo "nothing to do."  
	fi
	/bin/echo " done."
}

#warmup_system()
#{
#	if [ $1 -eq 1 ]; then
#		restart_tpcc
#	fi
#}

######    Main  ##########

for fault_type in 2 3 4 6 7 5
#for fault_type in 5
do
        for intensity in 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0
        do
        	if [ $EXPERIMENT_ID -eq 0 -o $EXPERIMENT_ID -eq 2 ]; then
        		        		
	        	primary_mongo_vms=`python /home/user/tejo/tejo/fault_injection_tools/liveness.py`
	        	secondary_mongo_vms=`python /home/user/tejo/tejo/fault_injection_tools/liveness.py secondary`
	        	
	        	#for all primaries
	        	
				while [ `echo $primary_mongo_vms|awk -F, '{print NF}'` -gt 0 ]
				do
				        target=`get_random_hostname $primary_mongo_vms`
				        primary_mongo_vms=`remove_hostname $primary_mongo_vms $target`
				        #warmup_system $EXPERIMENT_ID
						inject $target $fault_type $intensity $EXPERIMENT_ID
				done
				
				#for n secondaries
	
				secondary_mongo_vms=`pick_n_randomly $TRIES_PER_FAULT $secondary_mongo_vms`
	
				while [ `echo $secondary_mongo_vms|awk -F, '{print NF}'` -gt 0 ]
				do
				        target=`get_random_hostname $secondary_mongo_vms`
				        secondary_mongo_vms=`remove_hostname $secondary_mongo_vms $target`
				        #warmup_system $EXPERIMENT_ID
						inject $target $fault_type $intensity $EXPERIMENT_ID
				done
			elif [ $EXPERIMENT_ID -eq 1 -o $EXPERIMENT_ID -eq 3 ]; then
				target_vms=`pick_n_randomly $TRIES_PER_FAULT $vms`
	
				while [ `echo $target_vms|awk -F, '{print NF}'` -gt 0 ]
				do
				        target=`get_random_hostname $target_vms`
				        target_vms=`remove_hostname $target_vms $target`
				        #warmup_system $EXPERIMENT_ID
						inject $target $fault_type $intensity $EXPERIMENT_ID
				done
			fi
        
        done
done

/bin/echo "all done!"
