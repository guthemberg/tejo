#!/bin/sh

. /etc/svc.conf
. /home/user/svc/svc/experiments_scripts/db/volt/config

#copy main conf file
sh /home/user/svc/svc/common/deployment/run_anything.sh "scp monitor-001:/etc/svc.conf /tmp/;sudo cp /tmp/svc.conf /etc/"
ssh -o StrictHostKeyChecking=no workload-001 "scp monitor-001:/etc/svc.conf /tmp/;sudo cp /tmp/svc.conf /etc/"

echo -n 'stop all: '

#mongo wl
ssh -o StrictHostKeyChecking=no workload-001 sh /home/user/svc/svc/experiments_scripts/ycsb/stop.sh

#volt wl
ssh -o StrictHostKeyChecking=no workload-001 sh /home/user/svc/svc/experiments_scripts/tpcc/stop.sh
ssh -o StrictHostKeyChecking=no workload-001 sh /home/user/svc/svc/experiments_scripts/voter-selfcheck/stop.sh 

#stop and clean up 
sh /home/user/svc/svc/common/deployment/run_anything.sh "sudo service mongod stop"
#sh /home/user/svc/svc/common/deployment/run_anything.sh "sudo rm -rf /var/lib/mongodb/*;sudo rm -rf /var/log/mongodb/mongod.log;"

#ipfw rules
sh /home/user/svc/svc/common/deployment/run_anything.sh "sudo ipfw delete 60000 pipe 1 ip from any to any $mongo_ports keep-state; sudo ipfw pipe 1 delete;"
sh /home/user/svc/svc/common/deployment/run_anything.sh "sudo ipfw delete 60000 pipe 1 ip from any to any $volt_ports keep-state; sudo ipfw pipe 1 delete;"
echo -n 'done. '