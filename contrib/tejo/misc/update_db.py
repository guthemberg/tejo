import os
import socket
import rrdtool
import glob
import sys
from configobj import ConfigObj
import time,subprocess
from urllib2 import urlopen
import xmltodict


#db api available in home_dir
conf_file = "/etc/tejo.conf"
config=ConfigObj(conf_file)
sys.path.append(config['home_dir'])
ALIVE_TIME=int(config['alive_time'])
DEATH_TIME=int(config['time_to_vm_death'])
#from database import MyDB

#available in home_dir
from tejo.common.db.postgres.database import MyDB


path_to_vms_rrds=config['rrd_path_vms_prefix']+'/*.*'

dbconn=MyDB(config['db_name'],config['db_user'],config['db_host'],config['db_pass'])
query='drop table vm'
dbconn.genericRun(query)
sys.exit(0)

print path_to_vms_rrds

for vm in [(path.split('/')[-1]) for path in (glob.glob(path_to_vms_rrds))]:
    mongo_path=config['rrd_path_vms_prefix']+'/'+vm+'/mongodb*'
    for new_column in [(path.split('/')[-1]).split('.')[0] for path in (glob.glob(mongo_path))]:
        query='alter table vm add column %s numeric' % new_column
        dbconn.genericRun(query)
        query='alter table vm alter column %s SET NOT NULL' % new_column
        dbconn.genericRun(query)
        query='alter table vm alter column %s SET DEFAULT 0.0' % new_column
        dbconn.genericRun(query)
        print dbconn.getDebugMess()
    volt_path=config['rrd_path_vms_prefix']+'/'+vm+'/volt*'
    for new_column in [(path.split('/')[-1]).split('.')[0] for path in (glob.glob(volt_path))]:
        query='alter table vm add column %s numeric' % new_column
        dbconn.genericRun(query)
        query='alter table vm alter column %s SET NOT NULL' % new_column
        dbconn.genericRun(query)
        query='alter table vm alter column %s SET DEFAULT 0.0' % new_column
        dbconn.genericRun(query)
        print dbconn.getDebugMess()
    break
    

