/usr/bin/pkill -f run.sh ; 

if pgrep -f MyTPCC >/dev/null 2>&1; then sudo pkill -f MyTPCC; fi


/bin/rm -rf /tmp/slo_*