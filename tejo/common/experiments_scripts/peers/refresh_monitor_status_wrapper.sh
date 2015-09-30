#!/bin/sh

. /etc/tejo.conf

pkill -f refresh_monitor_status.py
/bin/tcsh -c "python ${home_dir}/tejo/common/experiments_scripts/peers/refresh_monitor_status.py  >& /tmp/refresh_monitor_status.log"

exit 0