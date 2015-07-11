#!/bin/sh

. /etc/svc.conf

i=0
while [ $i -eq 0 ]
do
	now=`date`
	echo -n "[${now}] stop workload... "
	if pgrep -f MyTPCC >/dev/null 2>&1; then sudo pkill -f MyTPCC; fi
	/bin/rm -rf /tmp/slo_*
	echo "done."
	echo -n "[${now}] restart cluster... "
	/bin/tcsh -c 'sh /home/user/svc/svc/experiments_scripts/db/volt/restart_cluster.sh 1 >& /tmp/volt_restart_cluster.log'
	echo "done."
	echo -n "[${now}] run workload... "
	/bin/tcsh -c 'cd /opt/voltdb/tests/test_apps/tpcc/;./run.sh clean'
	/bin/tcsh -c "cd /opt/voltdb/tests/test_apps/tpcc/;./run.sh client >& ${volt_wl_log}"
	echo "done."
done 
