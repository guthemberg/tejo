#!/bin/sh


echo "Fault Injection Script (bandwidth)"
FAULT_CODE="4"
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
DEFAULT_BWD="114Mbit/s"
BWD=$DEFAULT_BWD

DELETE_IPFW_RULES="sudo ipfw delete 60000 pipe 1 ip from any to any $mongo_ports keep-state; sudo ipfw pipe 1 delete;"
ADD_DEFAULT_IPFW_RULES="sudo ipfw add 60000 pipe 1 ip from any to any $mongo_ports keep-state; sudo ipfw pipe 1 config bw $BWD ;"
ADD_PREFIX_IPFW_RULES="sudo ipfw add 60000 pipe 1 ip from any to any $mongo_ports keep-state; sudo ipfw pipe 1 config bw "

if [ $SYSTEM_ID -eq 1 -o $SYSTEM_ID -eq 3 ]; then
	DELETE_IPFW_RULES="sudo ipfw delete 60000 pipe 1 ip from any to any $volt_ports keep-state; sudo ipfw pipe 1 delete;"
	ADD_DEFAULT_IPFW_RULES="sudo ipfw add 60000 pipe 1 ip from any to any $volt_ports keep-state; sudo ipfw pipe 1 config bw $BWD ;"
	ADD_PREFIX_IPFW_RULES="sudo ipfw add 60000 pipe 1 ip from any to any $volt_ports keep-state; sudo ipfw pipe 1 config bw "
fi

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
#	echo -n "checking system liveness... "
#	normal_flag=1
#	if [ $SYSTEM_ID -eq 1 ]; then
#		if [ `pgrep -f voltdb|wc -l` -eq 0 ]; then 
#			remove_fault_files
#			restart_tpcc
#			echo "tppc and voltd was restarted."
#			normal_flag=0
#			create_fault_files
#		fi
#	else
#		if [ `pgrep -f mongod|wc -l` -eq 0 ]; then
#			remove_fault_files
#			sudo service mongod restart
#			ssh -o StrictHostKeyChecking=no $ROUTER_HOST $REFRESH_COMMAND
#			/bin/sleep 2	
#			echo "mongod was restarted."
#			normal_flag=0
#			create_fault_files
#		fi
#	fi
#	if [ $normal_flag -eq 1 ]; then
#		echo "all right."
#	fi
#		
#}

delete_ipfw_rules()
{
	/bin/tcsh -c "$DELETE_IPFW_RULES"
}

add_ipfw_rules()
{
	/bin/tcsh -c "$ADD_PREFIX_IPFW_RULES $1 ;"
}

add_default_ipfw_rules()
{
	/bin/tcsh -c "$ADD_DEFAULT_IPFW_RULES"
}

inject()
{
	delete_ipfw_rules
	add_ipfw_rules "$1"
	echo -n "let's inject $1 for "
	echo -n "$2"
	echo " seconds..."
	/bin/sleep $2
	
	
#	now=`date +"%s"`
#	start=`date +"%s"`
#	passed=`expr $now - $start`
#	
#	remaining=`expr $2 - $passed`
#	
#	time_slot=10
#	
#	while [ $remaining -gt 0 ];
#	do
#			if [ $remaining -gt $time_slot ]; then
#				sleep $time_slot
#				check_system_liveness
#				passed=`expr $passed + $time_slot`
#			else
#				sleep $remaining
#				passed=`expr $passed + $remaining`
#			fi
#			remaining=`expr $2 - $passed`
#					
#	done 
	
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




######main


#value in bps
VALUE=1
BWD=""

if [ `echo "$INTENSITY == 1"|bc` -eq 1 ]; then
		VALUE="11000000"
        BWD="11Mbit/s"
elif [ `echo "$INTENSITY == .9"|bc` -eq 1 ]; then
		VALUE="20000000"
        BWD="20Mbit/s"
elif [ `echo "$INTENSITY == .8"|bc` -eq 1 ]; then
		VALUE="29000000"
        BWD="29Mbit/s"
elif [ `echo "$INTENSITY == .7"|bc` -eq 1 ]; then
		VALUE="38000000"
        BWD="38Mbit/s"
elif [ `echo "$INTENSITY == .6"|bc` -eq 1 ]; then
		VALUE="47000000"
        BWD="47Mbit/s"
elif [ `echo "$INTENSITY == .5"|bc` -eq 1 ]; then
		VALUE="56000000"
        BWD="56Mbit/s"
elif [ `echo "$INTENSITY == .4"|bc` -eq 1 ]; then
		VALUE="65000000"
        BWD="65Mbit/s"
elif [ `echo "$INTENSITY == .3"|bc` -eq 1 ]; then
		VALUE="74000000"
        BWD="74Mbit/s"
elif [ `echo "$INTENSITY == .2"|bc` -eq 1 ]; then
		VALUE="83000000"
        BWD="83Mbit/s"
elif [ `echo "$INTENSITY == .1"|bc` -eq 1 ]; then
		VALUE="92000000"
        BWD="92Mbit/s"
else  
        echo "no option"  
        exit  
fi

create_fault_files $FAULT_CODE $INTENSITY $VALUE

inject $BWD $DURATION


#going up, restoring normal rules

delete_ipfw_rules
add_default_ipfw_rules
remove_fault_files


refresh_system $SYSTEM_ID

echo -n "Done: "
/bin/date

exit 0