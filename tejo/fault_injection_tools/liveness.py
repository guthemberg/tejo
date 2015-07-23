import rrdtool
import sys
import time
from configobj import ConfigObj

#db api available in home_dir
conf_file = "/etc/tejo.conf"
config=ConfigObj(conf_file)
sys.path.append(config['home_dir'])
ALIVE_TIME=int(config['alive_time'])

def isVMAlive(hostname):
    #assuming that it is a storage VM
    alive=True
    try:
        rrd_file=config['rrd_path_vms_prefix']+"/"+hostname+"/"+config['vm_bytes_out_filename']
        alive=((long(time.time())-(rrdtool.info(rrd_file)["last_update"]))<=ALIVE_TIME)
    except:
        alive=False
    if alive:
        return True
    else:
        #supposing now that it is a workload VM
        try:
            rrd_file=config['rrd_path_workload_hosts_prefix']+"/"+hostname+"/"+config['slo_throughput_filename']
            return ((long(time.time())-(rrdtool.info(rrd_file)["last_update"]))<=ALIVE_TIME)
        except:
            return False


def get_mongodb_all_primary_replicas_vms():
    primary_replicas=""
    for hostname in config['vms']:
        try:
            if (int(rrdtool.info(config['rrd_path_vms_prefix']+"/"+hostname+"/"+config['vm_mongodb_is_primary_filename'])['ds[sum].last_ds'])==1) and (isVMAlive(hostname)):
                primary_replicas=primary_replicas+hostname+","
        except:
            pass
    if len(primary_replicas)>0:
        return primary_replicas[:-1]
    return primary_replicas

def get_mongodb_all_secondary_replicas_vms():
    secondary_replicas=""
    for hostname in config['vms']:
        try:
            if (int(rrdtool.info(config['rrd_path_vms_prefix']+"/"+hostname+"/"+config['vm_mongodb_is_primary_filename'])['ds[sum].last_ds'])==0) and (isVMAlive(hostname)):
                secondary_replicas=secondary_replicas+hostname+","
        except:
            pass
    if len(secondary_replicas)>0:
        return secondary_replicas[:-1]
    return secondary_replicas


#### main
if len(sys.argv)==1:
    sys.stdout.write(get_mongodb_all_primary_replicas_vms())
elif len(sys.argv)>1:
    if sys.argv[1] != 'secondary':
        sys.stdout.write(get_mongodb_all_primary_replicas_vms())
    else:
        sys.stdout.write(get_mongodb_all_secondary_replicas_vms())
        
