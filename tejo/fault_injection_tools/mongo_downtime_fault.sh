#!/bin/sh

FAULT_INJECTION_FILE=/tmp/fault_injection.txt
FAULT_INTENSITY_FILE=/tmp/fault_intensity.txt

DURATION=$1

ROUTER_HOST=ds1
REFRESH_COMMAND='sudo /usr/local/etc/rc.d/mongosd restart'

echo "Fault Injection Script"
echo -n "Start: "
/bin/date

#going down
sudo /usr/local/etc/rc.d/mongod stop
/bin/echo -n 1 > $FAULT_INJECTION_FILE
/bin/echo -n 1 > $FAULT_INTENSITY_FILE


echo -n "let's sleep for "
echo -n "$DURATION"
echo " seconds..."
/bin/sleep $DURATION

#going up
sudo /usr/local/etc/rc.d/mongod start
/bin/rm $FAULT_INJECTION_FILE $FAULT_INTENSITY_FILE

echo "let's sleep while before restarting. 60 seconds break..."
/bin/sleep 60

#refresh router
ssh $ROUTER_HOST $REFRESH_COMMAND

echo -n "Done: "
/bin/date