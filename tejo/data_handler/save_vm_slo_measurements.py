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

def isFailed(config,fault_flag,workload_hosts):
    result=0
    for host in workload_hosts:
        workload_host1_file=config['rrd_path_workload_hosts_prefix']+'/'+host+'/'+config['slo_violation_filename']
        if ((getFloatValue(workload_host1_file)>0.0) ) and (fault_flag>0):
            result=1

    #host2_file=config['rrd_path_hosts_prefix']+'/'+config['hosts'][1]+'/'+config['slo_violation_filename']
    #check host 1
#    if ((getFloatValue(host1_file)>0.0) or (getFloatValue(host2_file)>0.0)) and (fault_flag>0):
#        result=1
#    if ((getFloatValue(workload_host1_file)>0.0) ) and (fault_flag>0):
#        result=1
    return result
    

def insert_vm_stat_into_db(ts,hostname,dbconn,keys,failure,values):
    dbconn.genericRun("INSERT into vm (ts,hostname,failure,%s) VALUES (timestamp '%s','%s',%d,%s)" % (keys,ts,hostname,failure,values))

#def insert_fault_info_into_db(ts,hostname,dbconn,injection,intensity):
#    dbconn.genericRun("INSERT into fault (ts,hostname,injection,intensity) VALUES (timestamp '%s','%s',%d,%s)" % (ts,hostname,injection,intensity))

##this function expects ts as a string and throughput and violation as integers
def insert_slo_state_into_db(ts,dbconn,throughput,violation, \
                             target_throughput, \
                             system_id,active_vms, latency_95th,latency_99th,latency_avg,max_latency_95th,max_latency_99th,max_latency_avg):
    dbconn.genericRun("INSERT into slo (ts,throughput,violation,target_throughput,system_id,active_vms,latency_95th,latency_99th,latency_avg,max_latency_95th,max_latency_99th,max_latency_avg) VALUES (timestamp '%s',%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d)" % (ts,throughput,violation,target_throughput,system_id,active_vms,latency_95th,latency_99th,latency_avg,max_latency_95th,max_latency_99th,max_latency_avg))

##this function expects ts as a string and throughput and violation as integers
def insert_workload_state_into_db(ts,dbconn,hostname, throughput,violation, \
                             system_id, latency_95th,latency_99th,latency_avg):
    dbconn.genericRun("INSERT into workload (ts,hostname,throughput,violation,system_id,latency_95th,latency_99th,latency_avg) VALUES (timestamp '%s','%s',%d,%d,%d,%d,%d,%d)" % (ts,hostname,throughput,violation,system_id,latency_95th,latency_99th,latency_avg))

def format_db_value(db_value):
    return str(float(db_value))

def getFloatValue(rrd_file):
    return float(rrdtool.info(rrd_file)['ds[sum].last_ds'])

def get_host_path_id(hostname):
    if os.path.isdir(config['rrd_path_vms_prefix']+"/"+hostname) or os.path.isdir(config['rrd_path_workload_hosts_prefix']+"/"+hostname):
        return hostname
    else:
        ip=socket.gethostbyname(hostname)
        if os.path.isdir(config['rrd_path_vms_prefix']+"/"+ip) or os.path.isdir(config['rrd_path_workload_hosts_prefix']+"/"+ip):
            return ip
        else:
            return "unknown"
    
    
def isVMAlive(hostname):
    #assuming that it is a storage VM
    alive=True
    path_id=get_host_path_id(hostname)
    try:
        #try two files
        rrd_file=config['rrd_path_vms_prefix']+"/"+path_id+"/"+config['vm_bytes_out_filename']
        alive=((long(time.time())-(rrdtool.info(rrd_file)["last_update"]))<=ALIVE_TIME)
        if not alive:
            rrd_file=config['rrd_path_vms_prefix']+"/"+path_id+"/"+config['load_one_filename']
            alive=((long(time.time())-(rrdtool.info(rrd_file)["last_update"]))<=ALIVE_TIME)
    except:
        alive=False
    if alive:
        return True
    else:
        #supposing now that it is a workload VM
        try:
            rrd_file=config['rrd_path_workload_hosts_prefix']+"/"+path_id+"/"+config['slo_throughput_filename']
            return ((long(time.time())-(rrdtool.info(rrd_file)["last_update"]))<=ALIVE_TIME)
        except:
            return False

def isVMDead(hostname):
    #assuming that it is a storage VM
    dead=False
    path_id=get_host_path_id(hostname)
    try:
        #try two files
        rrd_file=config['rrd_path_vms_prefix']+"/"+path_id+"/"+config['vm_bytes_out_filename']
        dead=((long(time.time())-(rrdtool.info(rrd_file)["last_update"]))>DEATH_TIME)
        if not dead:
            rrd_file=config['rrd_path_vms_prefix']+"/"+path_id+"/"+config['load_one_filename']
            dead=((long(time.time())-(rrdtool.info(rrd_file)["last_update"]))>DEATH_TIME)
    except:
        dead=True
    if dead:
        return True
    else:
        #supposing now that it is a workload VM
        try:
            rrd_file=config['rrd_path_workload_hosts_prefix']+"/"+path_id+"/"+config['slo_throughput_filename']
            return ((long(time.time())-(rrdtool.info(rrd_file)["last_update"]))>DEATH_TIME)
        except:
            return True


def getIntValue(rrd_file):
    return int(float(rrdtool.info(rrd_file)['ds[sum].last_ds']))

def delete_path(path_to_be_deleted):
    #safeguard against accidents
    if len(path_to_be_deleted.split('/'))>5:
        subprocess.Popen(['sudo','rm', '-rf',path_to_be_deleted ], stdout=subprocess.PIPE, close_fds=True)

def check_node_list(list_of_nodes):
    dead_nodes=[]
    bad_nodes=[]
    good_nodes=[]
    for node in list_of_nodes:
        if isVMAlive(node):
            good_nodes.append(node)
        else:
            if isVMDead(node):
                dead_nodes.append(node)
            else:
                bad_nodes.append(node)  
                
    return (good_nodes,bad_nodes,dead_nodes)
        
        
    
def get_nodes():
    wls=[]
    vms=[]
    
    path_to_vms_rrds=config['rrd_path_vms_prefix']+'/*.*'
    vms,bad_nodes,dead_nodes=check_node_list([path.split('/')[-1] for path in (glob.glob(path_to_vms_rrds))])
    print "getting vms (vms:%d,bad_nodes:%d,dead_nodes:%d):"%(len(vms),len(bad_nodes),len(dead_nodes))
    print vms
    print bad_nodes
    print dead_nodes
    
    for node in dead_nodes:
        delete_path(config['rrd_path_vms_prefix']+'/'+node)
    
    path_to_wls_rrds=config['rrd_path_workload_hosts_prefix']+'/*.*'
    wls,bad_nodes,dead_nodes=check_node_list([path.split('/')[-1] for path in (glob.glob(path_to_wls_rrds))])
    print "getting wls (wls:%d,bad_nodes:%d,dead_nodes:%d):"%(len(wls),len(bad_nodes),len(dead_nodes))
    print wls
    print bad_nodes
    print dead_nodes
    
    for node in dead_nodes:
        delete_path(config['rrd_path_workload_hosts_prefix']+'/'+node)
    
    return (wls,vms)


def get_hostname(cluster,node_id):
    print cluster
    print node_id
    try:
        url=config['ganglia_api']+'/'+cluster+'/'+node_id
        print url
        document=urlopen(url)
        data=document.read()
        document.close()
        node=xmltodict.parse(data)
        for obj in node[u'GANGLIA_XML'][u'GRID'][u'CLUSTER'][u'HOST'][u'METRIC']:
            print obj
            if obj[u'@NAME']=='miscellaneous_hostname':
                return obj[u'@VAL']
        return node_id
    except:
        #trying through ssh
        #-i ${root_dir}/.ssh/id_rsa_cloud -o StrictHostKeyChecking=no
        rsa_key=config['root_dir']+'/.ssh/id_rsa_cloud'
        node_id = (subprocess.Popen(['ssh','-i',rsa_key,'-o','StrictHostKeyChecking=no',node_id,'hostname'], stdout=subprocess.PIPE, close_fds=True).communicate()[0].strip())
        return node_id
    
     
now = time.strftime("%c")
## Display current date and time from now variable 
print ("Current time %s"  % now )

#postgres db
dbconn=MyDB(config['db_name'],config['db_user'],config['db_host'],config['db_pass'])


rrd_path_vms_prefix=config['rrd_path_vms_prefix']
fault_injection_filename=config['fault_injection_filename']
fault_intensity_filename=config['fault_intensity_filename']
fault_value_filename=config['fault_value_filename']
rrd_path_workload_hosts_prefix=config['rrd_path_workload_hosts_prefix']
throughput_filename=config['slo_throughput_filename']
violation_filename=config['slo_violation_filename']
target_throughput_filename=config['slo_target_throughput_filename']
system_id_filename=config['slo_system_id_filename']
latency_95th_filename=config['slo_latency_95th_filename']
latency_99th_filename=config['slo_latency_99th_filename']
latency_avg_filename=config['slo_latency_avg_filename']
max_latency_95th_filename=config['slo_max_latency_95th_filename']
max_latency_99th_filename=config['slo_max_latency_99th_filename']
max_latency_avg_filename=config['slo_max_latency_avg_filename']

#rrd_file_prefix=config['rrd_file_prefix']

ts=time.strftime("%Y-%m-%d %H:%M:%S")


##collect slo status
throughput=0
violation=0
target_throughput=0
system_id=0
latency_95th=0
latency_99th=0
latency_avg=0
max_latency_95th=0
max_latency_99th=0
max_latency_avg=0

number_of_workloads=0
failed_data_collection=False
print "getting nodes..."
workload_hosts,vms=get_nodes()
print "number of wl nodes: %d" % len(workload_hosts)
print "number of vms nodes: %d" % len(vms)
#for hostname in config['workload_hosts']:
for hostname in workload_hosts:
    #if node is not found it return unknown
#    path_id=get_host_path_id(hostname)
    path_id=hostname
#     if not isVMAlive(hostname):
#         continue
    rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+latency_95th_filename
    node_latency_95th=getIntValue(rrd_file)
    
    rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+latency_99th_filename
    node_latency_99th=getIntValue(rrd_file)

    if (node_latency_95th>0 and node_latency_99th>0):
        
        latency_95th=latency_95th+node_latency_95th
        latency_99th=latency_99th+node_latency_99th
        
        rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+throughput_filename
        node_throughput=getIntValue(rrd_file)
        throughput=throughput+node_throughput
        
        rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+latency_avg_filename
        node_latency_avg=getIntValue(rrd_file)
        latency_avg=latency_avg+node_latency_avg
        
        rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+violation_filename
        node_violation=getIntValue(rrd_file)
        violation=violation+node_violation
        
        rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+target_throughput_filename
        target_throughput=target_throughput+getIntValue(rrd_file)
        
        rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+system_id_filename
        system_id=getIntValue(rrd_file)
        
        rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+max_latency_95th_filename
        max_latency_95th=getIntValue(rrd_file)
        
        rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+max_latency_99th_filename
        max_latency_99th=getIntValue(rrd_file)
        
        rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+max_latency_avg_filename
        max_latency_avg=getIntValue(rrd_file)
        
        number_of_workloads=number_of_workloads+1
    
        insert_workload_state_into_db(ts,dbconn,hostname, node_throughput, \
                                      node_violation, system_id, \
                                      node_latency_95th,node_latency_99th, \
                                      node_latency_avg)
    
if ((latency_95th<=0 or latency_99th<=0)) :
    failed_data_collection=True

if (number_of_workloads == 0) or failed_data_collection:
    print "workload is not running, nothing to do (latency_95th,latency_99th,number_of_workloads:%d,%d,%d)." % (latency_95th,latency_99th,number_of_workloads)
    print '[%s] Done.' % ts
    sys.exit(0)
    
latency_95th=int(latency_95th/number_of_workloads)
latency_99th=int(latency_99th/number_of_workloads)
latency_avg=int(latency_avg/number_of_workloads)


number_of_vms=0
#for hostname in config['vms']:
for node in vms:
    #if node is not found it return unknown
#    path_id=get_host_path_id(hostname)
    path_id=node
    stat={}
    list_of_files = (sorted(glob.glob(rrd_path_vms_prefix+"/"+path_id+"/*.rrd")))
    keys=""
    values=""
    #check fault injection
    fault_flag=0
    fault_file=rrd_path_vms_prefix+"/"+path_id+"/"+fault_injection_filename
    fault_intensity_file=rrd_path_vms_prefix+"/"+path_id+"/"+fault_intensity_filename
    fault_value_file=rrd_path_vms_prefix+"/"+path_id+"/"+fault_value_filename
    if getFloatValue(fault_file)>0.0:
        fault_flag=1
#     alive=True
    for filename in list_of_files:
#         if not isVMAlive(hostname):
#             alive=False
#             break
        db_key= ( (filename).split('/')[-1] ).split('.')[0]
        if len(keys)>0:
            keys+=(','+db_key)
        else:
            keys=db_key
        value=format_db_value(rrdtool.info(filename)['ds[sum].last_ds'])
        if len(values)>0:
            values+=(','+value)
        else:
            values=value
            
    #insert_fault_info_into_db(ts, hostname, dbconn, getIntValue(fault_file), str(getFloatValue(fault_intensity_file)), str(getFloatValue(fault_value_file)))
#     if alive:
    insert_vm_stat_into_db(ts,get_hostname(rrd_path_vms_prefix.split('/')[-1], node),dbconn,keys,isFailed(config, fault_flag,workload_hosts),values)
    number_of_vms = number_of_vms + 1

#save slo status
insert_slo_state_into_db(ts, dbconn, throughput, violation, \
                         target_throughput,system_id, \
                         number_of_vms,latency_95th,latency_99th,latency_avg, \
                         max_latency_95th,max_latency_99th,max_latency_avg)

print dbconn.getDebugMess()

print '[%s] Done.' % ts

sys.exit(0)


