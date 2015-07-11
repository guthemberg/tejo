#!/bin/sh

. /etc/svc.conf

now=`date +"%s"`
last_update=`stat -c %Y ${volt_wl_log}`
passed=`expr $now - $last_update`

if [ $passed -gt ${volt_wl_duration} ]; then
	if pgrep -f AsyncBenchmark >/dev/null 2>&1; then sudo pkill -f AsyncBenchmark; fi
	/bin/rm -rf /tmp/slo_* 
fi

exit 0
