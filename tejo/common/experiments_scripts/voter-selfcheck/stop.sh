/usr/bin/pkill -f run.sh ; 

if pgrep -f AsyncBenchmark >/dev/null 2>&1; then sudo pkill -f AsyncBenchmark; fi


/bin/rm -rf /tmp/slo_*

exit 0