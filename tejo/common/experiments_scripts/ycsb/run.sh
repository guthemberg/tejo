#!/bin/sh

. /etc/tejo.conf
#go to home
#root_dir=/home/user
#home_dir=${HOME}/svc
OUTPUT_DIR=${home_dir}/experiment_outputs
YCSB_HOME=${home_dir}/contrib/debian/mongodb/ycsb-0.1.4

#mongodb host
db_service="mongodb://datastore-001.svc.laas.fr:27017"

#read-only workload (C)
workload_label=wlC
ycsb_workload=${YCSB_HOME}/workloads/workloadc
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

if [ $# -eq 1 ]; then
	if [ $1 -ne 2 ]; then
		echo "invalid system_id option (must be 2). bye"
		exit -1
	fi
	system_id=$1
	label=reads_and_updates
	workload_file=${YCSB_HOME}/workloads/$label
elif [ $# -gt 1 ]; then
		echo "invalid number of parameters, expected a single additional paramet or none. bye"
		exit -1
fi

echo -n $system_id > /tmp/slo_system_id.txt



a=11

while [ $a -gt 10 ]
do
   echo $a
   a=`expr $a + 1`
	threads=30
	max_conn=2000
	ops_per_second=$DEFAULT_OPS_PER_SECOND
	now=`date`
	ts=`date +"%s"`
	echo "[${now}] Running YCSB with workload $workload_file and $ops_per_second operations/second..."
${ycsb_run_script} run mongodb -p mongodb.url=${db_service} -p mongodb.database="ycsb" -p mongodb.writeConcern="normal" -p mongodb.maxconnections=${max_conn} -threads ${threads} -target ${ops_per_second} -s -P ${workload_file} > ${OUTPUT_DIR}/${ts}_mongo_run_${label}_op_${ops_per_second}_op_per_sec_threads_${threads}_max_conn_${max_conn}.log 2>&1
	now=`date`
	echo "[${now}] Done YCSB with workload $workload_file and $ops_per_second operations/second, threads ${threads}, max_conn equals to ${max_conn}."
	echo "[INFINITY LOOPING] sleeping 0 (non-stop) seconds before next iteraction..."
done

echo $a

exit

#a=0
#for threads in 2 4 6 8 10 12 14 16 18 20 22 24 28 32 36 40 44 48 50 64 100 128 200 256 500
#{
#        for max_conn in 10 20 40 80 100 160 320 500 1000 1500 2000 2500 3000 3500 4000 4500 5000
#        {
#		ops_per_second=5000
#		now=`date`
#		a=`expr $a + 1`
#		echo $a
#		ts=`date +"%s"`
#		ycsb_workload=${YCSB_HOME}/workloads/workloadc.0
#		echo "[${now}] Running YCSB with workload $ycsb_workload and $ops_per_second operations/second..."
#		${ycsb_run_script} run mongodb -p mongodb.url=${db_service} -p mongodb.database="ycsb" -p mongodb.writeConcern="normal" -p mongodb.maxconnections=${max_conn} -threads ${threads} -target ${ops_per_second} -s -P ${ycsb_workload} > ${OUTPUT_DIR}/${ts}_mongo_run_${workload_label}_${n_requests}_op_${ops_per_second}_op_per_sec_threads_${threads}_max_conn_${max_conn}.log 2>&1
#        	now=`date`
#		echo "[${now}] Done YCSB with workload $ycsb_workload and $ops_per_second operations/second, threads ${threads}, max_conn equals to ${max_conn}."
#		echo "[END LOOPING] sleeping 2 seconds before next iteraction..."
#		sleep 2
#	}
#}
#exit

a=0

#for threads in 2 4 8 10 16 32 50 64 100 128 200 256 500
for threads in 2 4 6 8 10 12 14 16 18 20 22 24 28 32 36 40 44 48 50 64 100 128 200 256 500
#10 50 100 200 500
{
        for max_conn in 10 20 40 80 100 160 320 500 1000 1500 2000 2500 3000 3500 4000 4500 5000
        {
		ops_per_second=1000
		now=`date`
		a=`expr $a + 1`
		echo $a
		ts=`date +"%s"`
		ycsb_workload=${YCSB_HOME}/workloads/workloadc.0
		echo "[${now}] Running YCSB with workload $ycsb_workload and $ops_per_second operations/second..."
		${ycsb_run_script} run mongodb -p mongodb.url=${db_service} -p mongodb.database="ycsb" -p mongodb.writeConcern="normal" -p mongodb.maxconnections=${max_conn} -threads ${threads} -target ${ops_per_second} -s -P ${ycsb_workload} > ${OUTPUT_DIR}/${ts}_mongo_run_${workload_label}_${n_requests}_op_${ops_per_second}_op_per_sec_threads_${threads}_max_conn_${max_conn}.log 2>&1
        	now=`date`
		echo "[${now}] Done YCSB with workload $ycsb_workload and $ops_per_second operations/second, threads ${threads}, max_conn equals to ${max_conn}."
		echo "[END LOOPING] sleeping 2 seconds before next iteraction..."
		sleep 2
	}
}
exit

#for ops_per_second in 1000 2000 3000 4000 5000 6000 7000 8000 9000 10000 11000 12000 13000 14000 15000 16000 17000 18000 19000 20000 21000 22000 24000 25000 26000 27000 28000 29000 30000 31000 32000
#for ops_per_second in 13000 14000 15000 16000 17000 18000 19000 20000 21000 22000 24000 25000 26000 27000 28000 29000 30000 31000 32000
#for ops_per_second in 22000 24000 25000 26000 27000 28000 29000 30000 31000 32000
a=11

while [ $a -gt 10 ]
do
   echo $a
   a=`expr $a + 1`
	threads=2
	ops_per_second=MAX
	max_conn=100
	ops_per_second=1000
	now=`date`
	ts=`date +"%s"`
	echo "[${now}] Running YCSB with workload $ycsb_workload and $ops_per_second operations/second..."
	${ycsb_run_script} run mongodb -p mongodb.url=${db_service} -p mongodb.database="ycsb" -p mongodb.writeConcern="normal" -p mongodb.maxconnections=${max_conn} -threads ${threads} -target ${ops_per_second} -s -P ${ycsb_workload} > ${OUTPUT_DIR}/${ts}_mongo_run_${workload_label}_${n_requests}_op_${ops_per_second}_op_per_sec_threads_${threads}_max_conn_${max_conn}.log 2>&1
	now=`date`
			echo "[${now}] Done YCSB with workload $ycsb_workload and $ops_per_second operations/second, threads ${threads}, max_conn equals to ${max_conn}."
			echo "[INFINITY LOOPING] sleeping 0 (non-stop) seconds before next iteraction..."
#			sleep 2 
done

echo $a

exit

for ops_per_second in MAX
{
	now=`date`
	echo "[${now}] Running YCSB with workload $ycsb_workload and $ops_per_second operations/second..."
#	for threads in 2 10 50 100 200 500
#	for threads in 50 100 150 200 300 500
#	for threads in 150 200 300 500 600 700
#	for threads in 2 5 10 20 30 40 50
	for threads in 35 40 45
	{
#		for max_conn in 10 100 1000
#		for max_conn in 100 500 1000 1500 2000
#		for max_conn in 1000 2000 3000 4000 5000
#		for max_conn in 100 500 1000 2000
#		for max_conn in 100 200 300 400 500 600 700 800 900 1000 2000
		for max_conn in 100 200 300 400 500 600 700 800 900 1000 1100 1200 1300 1400 1500 1600 1700 1800 1900 2000 2500 3000
#		for max_conn in 1000 2000 3000 4000 5000 6000 7000
		{
			echo "[${now}] Running YCSB with workload $ycsb_workload and $ops_per_second operations/second, threads ${threads}, max_conn equals to ${max_conn}."
#			${ycsb_run_script} run mongodb -p mongodb.url=${db_service} -p mongodb.database="ycsb" -p mongodb.writeConcern="normal" -p mongodb.maxconnections=${max_conn} -threads ${threads} -target $ops_per_second -s -P ${ycsb_workload} > ${OUTPUT_DIR}/mongo_run_${workload_label}_${n_requests}_op_${ops_per_second}_op_per_sec_threads_${threads}_max_conn_${max_conn}.log 2>&1
			${ycsb_run_script} run mongodb -p mongodb.url=${db_service} -p mongodb.database="ycsb" -p mongodb.writeConcern="normal" -p mongodb.maxconnections=${max_conn} -threads ${threads} -s -P ${ycsb_workload} > ${OUTPUT_DIR}/mongo_run_${workload_label}_${n_requests}_op_${ops_per_second}_op_per_sec_threads_${threads}_max_conn_${max_conn}.log 2>&1
			now=`date`
			echo "[${now}] Done YCSB with workload $ycsb_workload and $ops_per_second operations/second, threads ${threads}, max_conn equals to ${max_conn}."
			echo "sleeping 2 seconds before next iteraction..."
			sleep 2 
		}
	}
	now=`date`
	echo "[${now}] Done YCSB with workload $ycsb_workload and $ops_per_second operations/second."
	echo "sleeping 10 minutes before next round (throughput rate)..."
	sleep 600
}

