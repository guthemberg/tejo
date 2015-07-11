#!/bin/sh



#how to call is
# sh run.sh
# or
# sh run.sh SYSTEM_ID OPERATIONS_PER_SECOND
#where 	SYSTEM_ID might be 0 or 2
#		OPERATION PER SECOND 50
. /etc/tejo.conf

sudo chmod ugo+x ${home_dir}/contrib/fedora/mongodb/ycsb-0.1.4/bin/ycsb


#go to home
#root_dir=/home/user
#home_dir=${HOME}/svc
OUTPUT_DIR=/tmp/experiment_outputs
YCSB_HOME=${home_dir}/contrib/fedora/mongodb/ycsb-0.1.4

#mongodb host
db_service="mongodb://${mongo_query_router_host}:27017"

#read-only workload (C)
workload_label=wlC
ycsb_run_script=${YCSB_HOME}/bin/ycsb
n_requests=1200K
DEFAULT_OPS_PER_SECOND=3000

if [ ! -d "$OUTPUT_DIR" ]; then
	mkdir ${OUTPUT_DIR}
fi

#mongodb identifier

system_id=0
label=read_only
workload_file=${YCSB_HOME}/workloads/$label
threads=30
max_conn=2000

defaultl_core_file=${home_dir}/contrib/fedora/mongodb/ycsb-0.1.4/core/lib/core-0.1.4.jar
backup_core_file=${root_dir}/core-0.1.4.jar
if [ ! -e backup_core_file ]; then
	cp $defaultl_core_file $backup_core_file
fi

if [ $# -eq 0 ]; then
	sed "s|RECORDCOUNT|$mongo_recordcount|g" ${YCSB_HOME}/workloads/$label | sed "s|MAXTIME|$mongo_maxexecutiontime|g" | sed "s|OPCOUNT|$DEFAULT_OPS_PER_SECOND|g"  > /tmp/myworload
	workload_file=/tmp/myworload
	cp $backup_core_file $defaultl_core_file 
elif [ $# -eq 1 ]; then
	if [ $1 -ne 2 ]; then
		echo "invalid system_id option (must be 2). bye"
		exit -1
	fi
	system_id=$1
	label=reads_and_updates
	sed "s|RECORDCOUNT|$mongo_recordcount|g" ${YCSB_HOME}/workloads/$label | sed "s|MAXTIME|$mongo_maxexecutiontime|g" | sed "s|OPCOUNT|$DEFAULT_OPS_PER_SECOND|g"  > /tmp/myworload
	workload_file=/tmp/myworload
	#	workload_file=${YCSB_HOME}/workloads/$label
	cp $backup_core_file $defaultl_core_file 
elif [ $# -eq 2 ]; then
	if [ $1 -eq 2 ]; then
		system_id=$1
		label=reads_and_updates
		workload_file=${YCSB_HOME}/workloads/$label	
		DEFAULT_OPS_PER_SECOND=$2	
	elif [ $1 -eq 0 ]; then
		DEFAULT_OPS_PER_SECOND=$2	
	else
		echo "invalid system_id option (must be 0 or 2). bye"
		exit -1
	fi
	threads=2
	max_conn=10
	operations=`echo "${DEFAULT_OPS_PER_SECOND}*${mongo_maxexecutiontime}"|bc`
	if [ ! -e ${home_dir}/contrib/fedora/mongodb/ycsb-0.1.4_core_${DEFAULT_OPS_PER_SECOND}op.jar ]; then
		echo "core.far does not exit, bye."
		exit 1
	fi
	cp ${home_dir}/contrib/fedora/mongodb/ycsb-0.1.4_core_${DEFAULT_OPS_PER_SECOND}op.jar ${home_dir}/contrib/fedora/mongodb/ycsb-0.1.4/core/lib/core-0.1.4.jar
	sed "s|RECORDCOUNT|$mongo_recordcount|g" ${YCSB_HOME}/workloads/$label | sed "s|MAXTIME|$mongo_maxexecutiontime|g" | sed "s|OPCOUNT|$operations|g"  > /tmp/myworload
	workload_file=/tmp/myworload
		
elif [ $# -gt 2 ]; then
		echo "invalid number of parameters, expected a single additional paramet or none. bye"
		exit -1
fi

echo -n $system_id > /tmp/slo_system_id.txt



a=11

while [ $a -gt 10 ]
do
   echo $a
   a=`expr $a + 1`
	ops_per_second=$DEFAULT_OPS_PER_SECOND
	now=`date`
	ts=`date +"%s"`
	echo "[${now}] Running YCSB with workload $workload_file and $ops_per_second operations/second..."
${ycsb_run_script} run mongodb -p mongodb.url=${db_service} -p mongodb.database="ycsb" -p mongodb.writeConcern="normal" -p mongodb.maxconnections=${max_conn} -threads ${threads} -target ${ops_per_second} -s -P ${workload_file} > ${OUTPUT_DIR}/${ts}_mongo_run_${label}_op_${ops_per_second}_op_per_sec_threads_${threads}_max_conn_${max_conn}.log 2>&1
	now=`date`
	echo "[${now}] Done YCSB with workload $workload_file and $ops_per_second operations/second, threads ${threads}, max_conn equals to ${max_conn}."
	echo "[INFINITY LOOPING] sleeping 0 (non-stop) seconds before next interaction..."
done

echo $a

exit



