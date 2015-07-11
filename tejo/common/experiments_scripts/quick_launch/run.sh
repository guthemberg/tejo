#!/bin/sh

. /etc/svc.conf
. /home/user/svc/svc/experiments_scripts/db/volt/config

#stop all
sh /home/user/svc/svc/experiments_scripts/quick_launch/stop.sh

#copy main conf file
sh /home/user/svc/svc/common/deployment/run_anything.sh "scp monitor-001:/etc/svc.conf /tmp/;sudo cp /tmp/svc.conf /etc/"
ssh -o StrictHostKeyChecking=no workload-001 "scp monitor-001:/etc/svc.conf /tmp/;sudo cp /tmp/svc.conf /etc/"
	
#add ipfw rules
if [ $EXPERIMENT_ID -eq 0 -o $EXPERIMENT_ID -eq 2 ]; then
	sh /home/user/svc/svc/common/deployment/run_anything.sh "sudo ipfw add 60000 pipe 1 ip from any to any $mongo_ports keep-state ;sudo ipfw pipe 1 config bw 114Mbit/s"
	sh /home/user/svc/svc/common/deployment/run_anything.sh "sudo service mongod start"
	if [ $EXPERIMENT_ID -eq 2 ]; then
		ssh -o StrictHostKeyChecking=no workload-001 sh /home/user/svc/svc/experiments_scripts/ycsb/run.sh $EXPERIMENT_ID
	else
		ssh -o StrictHostKeyChecking=no workload-001 sh /home/user/svc/svc/experiments_scripts/ycsb/run.sh
	fi
elif [ $EXPERIMENT_ID -eq 1 -o $EXPERIMENT_ID -eq 3 ]; then
	sh /home/user/svc/svc/common/deployment/run_anything.sh "sudo ipfw add 60000 pipe 1 ip from any to any $volt_ports keep-state ;sudo ipfw pipe 1 config bw 114Mbit/s;"
	if [ $EXPERIMENT_ID -eq 1 ]; then
		ssh -o StrictHostKeyChecking=no workload-001 sh /home/user/svc/svc/experiments_scripts/tpcc/run.sh
	else
		ssh -o StrictHostKeyChecking=no workload-001 sh /home/user/svc/svc/experiments_scripts/voter-selfcheck/run.sh
	fi
else
	echo "wrong EXPERIMENT_ID value, $EXPERIMENT_ID , bye.".
	exit -1
fi
