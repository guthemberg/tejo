#!/bin/sh



#how to call is
# sh run.sh
# or
# sh run.sh SYSTEM_ID OPERATIONS_PER_SECOND
#where 	SYSTEM_ID might be 0 or 2
#		OPERATION PER SECOND 50
. /etc/tejo.conf


rm $mongo_active_wl_file

/usr/bin/pkill -f run.sh ; /usr/bin/pkill -f ycsb-0.1.4 ; /bin/rm -rf /tmp/slo_*; cd /home/`whoami`; sudo rm -rf /tmp/experiment_outputs ; sudo mkdir /tmp/experiment_outputs; sudo chown `whoami` /tmp/experiment_outputs 
