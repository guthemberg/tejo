#!/bin/sh


echo "Fault Injection Script (memory)"
FAULT_CODE="5"
echo -n "Start: "
/bin/date

. /etc/tejo.conf

DURATION=$1
INTENSITY=$2
#running db+tppc
#0 for mongodb + ycsb read-oly
#1 for voltdb + tppc
SYSTEM_ID=$3

FAULT_INJECTION_FILE=/tmp/fault_injection.txt
FAULT_INTENSITY_FILE=/tmp/fault_intensity.txt
FAULT_VALUE_FILE=/tmp/fault_value.txt

ROUTER_HOST=$mongo_query_router_host
REFRESH_COMMAND='sudo /usr/local/etc/rc.d/mongosd restart'


remove_fault_files()
{
	/bin/rm $FAULT_INJECTION_FILE $FAULT_INTENSITY_FILE $FAULT_VALUE_FILE
}

create_fault_files()
{
#set codes
	/bin/echo -n $1 > $FAULT_INJECTION_FILE
	/bin/echo -n $2 > $FAULT_INTENSITY_FILE
	/bin/echo -n $3 > $FAULT_VALUE_FILE
}

#check_system_liveness()
#{
	#echo -n "checking system liveness... "
	#normal_flag=1
#
#	start=`date +"%s"`	
#
#	if [ $SYSTEM_ID -eq 1 ]; then
#		if [ `pgrep -f voltdb|wc -l` -eq 0 ]; then 
#			remove_fault_files
#			restart_tpcc
#			#echo "tppc and voltd was restarted."
#			#normal_flag=0
#			create_fault_files
#		fi
#	else
#		if [ `pgrep -f mongod|wc -l` -eq 0 ]; then
#			remove_fault_files
#			sudo service mongod restart
#			ssh -o StrictHostKeyChecking=no $ROUTER_HOST $REFRESH_COMMAND
#			/bin/sleep 2	
#			#echo "mongod was restarted."
#			#normal_flag=0
#			create_fault_files
#		fi
#	fi
	#if [ $normal_flag -eq 1 ]; then
#		#echo "all right."
	#fi
#		
#	now=`date +"%s"`
#	echo `expr $now - $start`
#	
#}

inject()
{
	echo -n "let's inject $1 for "
	echo -n "$2"
	echo " seconds..."


	VALUE=$1
	DURATION=$2
	
	now=`date +"%s"`
	start=`date +"%s"`
	passed=`expr $now - $start`
	sum=`expr $now + $DURATION`
	
	remaining=`expr $DURATION - $passed`
	
#echo $VALUE
#echo $remaining
#exit
	while [ $now -lt $sum ];
	do
	        /bin/tcsh -c "python /home/user/tejo/tejo/fault_injection_tools/eat_memory.py $VALUE $remaining"
	        now=`date +"%s"`
	        passed=`expr $now - $start`
			remaining=`expr $DURATION - $passed`
	done 
	
}

refresh_system()
{
	if [ $1 -eq 0 -o $1 -eq 2 ]; then
#refresh router
		/bin/sleep 10
		ssh -o StrictHostKeyChecking=no $ROUTER_HOST $REFRESH_COMMAND
#refresh again, sometimes it fails at the first call
		/bin/sleep 10
		ssh -o StrictHostKeyChecking=no $ROUTER_HOST $REFRESH_COMMAND
		/bin/sleep 10
	fi
}

#########main



#value in bps
VALUE=1

if [ `echo "$INTENSITY == 1.0"|bc` -eq 1 ]; then
		VALUE="0.97"
elif [ `echo "$INTENSITY == .9"|bc` -eq 1 ]; then
		VALUE="0.94"
elif [ `echo "$INTENSITY == .8"|bc` -eq 1 ]; then
		VALUE="0.91"
elif [ `echo "$INTENSITY == .7"|bc` -eq 1 ]; then
		VALUE="0.88"
elif [ `echo "$INTENSITY == .6"|bc` -eq 1 ]; then
		VALUE="0.85"
elif [ `echo "$INTENSITY == .5"|bc` -eq 1 ]; then
		VALUE="0.82"
elif [ `echo "$INTENSITY == .4"|bc` -eq 1 ]; then
		VALUE="0.79"
elif [ `echo "$INTENSITY == .3"|bc` -eq 1 ]; then
		VALUE="0.76"
elif [ `echo "$INTENSITY == .2"|bc` -eq 1 ]; then
		VALUE="0.73"
elif [ `echo "$INTENSITY == .1"|bc` -eq 1 ]; then
		VALUE="0.70"
else  
        echo "no option"  
        exit  
fi


create_fault_files $FAULT_CODE $INTENSITY $VALUE

inject $VALUE $DURATION


remove_fault_files


refresh_system $SYSTEM_ID

echo -n "Done: "
/bin/date

exit