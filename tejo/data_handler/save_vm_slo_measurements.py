import os
import socket
import rrdtool
import glob
import sys
from configobj import ConfigObj
import time,subprocess
from urllib2 import urlopen
import xmltodict
import pickle

#db api available in home_dir
conf_file = "/etc/tejo.conf"
config=ConfigObj(conf_file)
sys.path.append(config['home_dir'])
ALIVE_TIME=int(config['alive_time'])
DEATH_TIME=int(config['time_to_vm_death'])
#from database import MyDB

#available in home_dir
from tejo.common.db.postgres.database import MyDB

hostname_table_file='/tmp/hostname_table.pck'

failed_hostnames='/tmp/failed_hostname_table.pck'


def save_object_to_file(myobject,output_file):
    f = open(output_file,'w')
    pickle.dump(myobject, f)
    f.close()

def load_object_from_file(input_file):
    return pickle.load( open( input_file, "rb" ) )

failed_host_table={}
if os.path.isfile(failed_hostnames):
    failed_host_table = load_object_from_file(failed_hostnames)
else:
    save_object_to_file(failed_host_table, failed_hostnames)


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
    

def insert_vm_stat_into_db(ts,hostname,dbconn,keys,failure,values,location):
    dbconn.genericRun("INSERT into vm (ts,hostname,failure,%s,location) VALUES (timestamp '%s','%s',%d,%s,'%s')" % (keys,ts,hostname,failure,values,location))

def insert_monitor_stat_into_db(ts,hostname,dbconn,keys,values,location):
    dbconn.genericRun("INSERT into monitor (ts,hostname,%s,location) VALUES (timestamp '%s','%s',%s,'%s')" % (keys,ts,hostname,values,location))

#def insert_fault_info_into_db(ts,hostname,dbconn,injection,intensity):
#    dbconn.genericRun("INSERT into fault (ts,hostname,injection,intensity) VALUES (timestamp '%s','%s',%d,%s)" % (ts,hostname,injection,intensity))

##this function expects ts as a string and throughput and violation as integers
def insert_slo_state_into_db(ts,dbconn,throughput,violation, \
                             target_throughput, \
                             system_id,active_vms, latency_95th,latency_99th, \
                             latency_avg,max_latency_95th,max_latency_99th, \
                             max_latency_avg, location,number_of_workloads):
    dbconn.genericRun("INSERT into slo (ts,throughput,violation,target_throughput,system_id,active_vms,latency_95th,latency_99th,latency_avg,max_latency_95th,max_latency_99th,max_latency_avg,location,number_of_workloads) VALUES (timestamp '%s',%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,'%s',%d)" % (ts,throughput,violation,target_throughput,system_id,active_vms,latency_95th,latency_99th,latency_avg,max_latency_95th,max_latency_99th,max_latency_avg,location,number_of_workloads))

##this function expects ts as a string and throughput and violation as integers
def insert_workload_state_into_db(ts,dbconn,hostname, throughput,violation, \
                             system_id, latency_95th,latency_99th,latency_avg, \
                             rtt,location,target_throughput,outliers, \
                             service_rtt):
    dbconn.genericRun("INSERT into workload (ts,hostname,throughput,violation,system_id,latency_95th,latency_99th,latency_avg,rtt,location,target_throughput,outliers,service_rtt) VALUES (timestamp '%s','%s',%d,%d,%d,%d,%d,%d,%.4f,'%s',%d,%d,%.4f)" % (ts,hostname,throughput,violation,system_id,latency_95th,latency_99th,latency_avg,rtt,location,target_throughput,outliers,service_rtt))

def format_db_value(db_value):
    return str(float(db_value))

def getFloatValue(rrd_file):
    return float(rrdtool.info(rrd_file)['ds[sum].last_ds'])

def get_host_path_id(hostname):
    #rrd_path_monitor_prefix
    if os.path.isdir(config['rrd_path_vms_prefix']+"/"+hostname) or os.path.isdir(config['rrd_path_workload_hosts_prefix']+"/"+hostname) or os.path.isdir(config['rrd_path_monitor_prefix']+"/"+hostname):
        return hostname
    else:
        ip=socket.gethostbyname(hostname)
        if os.path.isdir(config['rrd_path_vms_prefix']+"/"+ip) or os.path.isdir(config['rrd_path_workload_hosts_prefix']+"/"+ip) or os.path.isdir(config['rrd_path_monitor_prefix']+"/"+ip):
            return ip
        else:
            return "unknown"



# config['rrd_path_workload_hosts_prefix']
# config['slo_throughput_filename']    
def isPeerAlive(path_to_rrd,rrd_filename,peer):
    path_id=get_host_path_id(peer)    
    try:
        rrd_file=path_to_rrd+"/"+path_id+"/"+rrd_filename
        return ((long(time.time())-(rrdtool.info(rrd_file)["last_update"]))<=ALIVE_TIME)
    except:
        return False

#config['rrd_path_workload_hosts_prefix']
#config['slo_throughput_filename']
def isPeerDead(path_to_rrd,rrd_filename,peer):
    #assuming that it is a storage VM
    path_id=get_host_path_id(peer)
    try:
        rrd_file=path_to_rrd+"/"+path_id+"/"+rrd_filename
        return ((long(time.time())-(rrdtool.info(rrd_file)["last_update"]))>DEATH_TIME)
    except:
        return True

    
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
            alive=False
    if alive:
        return True
    else:
        #supposing now that it is a monitor VM
        try:
            rrd_file=config['rrd_path_monitor_prefix']+"/"+path_id+"/"+config['load_one_filename']
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
            dead=True
    if dead:
        return True
    else:
        #supposing now that it is a monitor VM
        try:
            rrd_file=config['rrd_path_monitor_prefix']+"/"+path_id+"/"+config['load_one_filename']
            return ((long(time.time())-(rrdtool.info(rrd_file)["last_update"]))>DEATH_TIME)
        except:
            return True

def isNodeDead(path_to_rrd,hostname):
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

# def getFloatValue(rrd_file):
#     return (float(rrdtool.info(rrd_file)['ds[sum].last_ds']))




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
                
    return (good_nodes,dead_nodes,bad_nodes)
        
        
    
def get_nodes(setup_peers_status,hostname_table):
#     wls=[]
#     vms=[]
    
    path_to_vms_rrds=config['rrd_path_vms_prefix']+'/*.*'
    vms,dead_nodes=check_node_list([path.split('/')[-1] for path in (glob.glob(path_to_vms_rrds))])[:2]
#     print "getting vms (vms:%d,bad_nodes:%d,dead_nodes:%d):"%(len(vms),len(bad_nodes),len(dead_nodes))
#     print vms
#     print bad_nodes
#     print dead_nodes
    
    for node in dead_nodes:
        delete_path(config['rrd_path_vms_prefix']+'/'+node)

    ##do the same for  monitor
    path_to_monitors_rrds=config['rrd_path_monitor_prefix']+'/*.*'
    monitors,dead_nodes=check_node_list([path.split('/')[-1] for path in (glob.glob(path_to_monitors_rrds))])[:2]
    for node in dead_nodes:
        delete_path(config['rrd_path_monitor_prefix']+'/'+node)


    
    path_to_wls_rrds=config['rrd_path_workload_hosts_prefix']+'/*.*'
    wls,dead_nodes=check_node_list([path.split('/')[-1] for path in (glob.glob(path_to_wls_rrds))])[:2]
    
#     print "getting wls (wls:%d,bad_nodes:%d,dead_nodes:%d):"%(len(wls),len(bad_nodes),len(dead_nodes))
#     print wls
#     print bad_nodes
#     print dead_nodes
    
    rrd_path_workload_hosts_prefix=config['rrd_path_workload_hosts_prefix']
    for node in dead_nodes:
        (node_name,hostname_table)=check_hostname(rrd_path_workload_hosts_prefix.split('/')[-1],config['workload_user'],node,hostname_table)
        if node_name in setup_peers_status:
            setup_peers_status[node_name]['active']=False
            setup_peers_status[node_name]['dead']=True
        delete_path(config['rrd_path_workload_hosts_prefix']+'/'+node)
    
    return (wls,vms,monitors,setup_peers_status,hostname_table)


def get_hostname_table():
    hostname_table={}
    if os.path.isfile(hostname_table_file):
        hostname_table=load_object_from_file(hostname_table_file)
    else:
        save_object_to_file(hostname_table, hostname_table_file)
    return hostname_table

def get_hostname(cluster,username,node_id, hostname_table):
#     print cluster
#     print node_id
    if node_id in hostname_table:
        #print "found in table:%s:%s"%(node_id,hostname_table[node_id])
        return hostname_table[node_id],hostname_table

    try:
        #print "hostname try: %s"%node_id
        url=config['ganglia_api']+'/'+cluster+'/'+node_id
#         print url
        document=urlopen(url)
        data=document.read()
        document.close()
        node=xmltodict.parse(data)
        for obj in node[u'GANGLIA_XML'][u'GRID'][u'CLUSTER'][u'HOST'][u'METRIC']:
#             print obj
            if obj[u'@NAME']=='miscellaneous_hostname':
                new_hostname=obj[u'@VAL']
                hostname_table[node_id]=new_hostname
                return (new_hostname,hostname_table)
        return (node_id,hostname_table)
    except:
        #print "hostname try again: %s"%node_id
        #trying through ssh
        #-i ${root_dir}/.ssh/id_rsa_cloud -o StrictHostKeyChecking=no
        
        ###known exceptions
        if node_id in failed_host_table:
            if failed_host_table[node_id]>12:
                #print "known bad node %s" % node_id
                return (node_id,hostname_table)
            
        
        rsa_key=config['root_dir']+'/.ssh/id_rsa_cloud'
        destination=username+'@'+node_id
        cmd = (subprocess.Popen(['ssh','-i',rsa_key,'-o','StrictHostKeyChecking=no', '-o', 'PasswordAuthentication=no', '-o','ConnectTimeout=5' ,'-o', 'ServerAliveInterval=5',destination,'hostname'], stdout=subprocess.PIPE, close_fds=True))
        new_node_id=cmd.communicate()[0].strip()
        if cmd.returncode == 0:
            #print "add to table:%s:%s"%(node_id,new_node_id)
            hostname_table[node_id]=new_node_id            
            return new_node_id,hostname_table
        #print "ssh to %s failed"%node_id
        fails_counter=1
        if node_id in failed_host_table:
            fails_counter=failed_host_table[node_id]+1
        failed_host_table[node_id]=fails_counter
        save_object_to_file(failed_host_table, failed_hostnames)        
        return (node_id,hostname_table)

def check_hostname(cluster,username,name,hostname_table):
    try:
        int(name.split('.')[-1])
        return (get_hostname(cluster, username,name,hostname_table))
    except:
        ##this means that the hostname is ok!!!
        return (name,hostname_table)
#exclude some selected, troubled rrd files
def is_it_an_invalid_rrd_file(name):
    if 'diskstat' in name:
        if 'sda' in name:
            False
        else:
            return True
    return False
 
def close_ssh_tunnel_to_master_db():
#    rsa_key=config['root_dir']+'/.ssh/id_rsa_cloud'
    process_key=config['guest_vm_sys_user']+'@'+config['db_master']
    (subprocess.Popen(['pkill','-f',process_key], stdout=subprocess.PIPE, close_fds=True).communicate()[0].strip())

def open_ssh_tunnel_to_master_db():
    close_ssh_tunnel_to_master_db()
    rsa_key=config['root_dir']+'/.ssh/id_rsa_cloud'
    process_key=config['guest_vm_sys_user']+'@'+config['db_master']
    while len(subprocess.Popen(['ssh','-i',rsa_key,'-o','StrictHostKeyChecking=no',config['db_master'],'pgrep','-f',process_key], stdout=subprocess.PIPE, close_fds=True).communicate()[0].strip())>0:
        print 'waiting to old tunnel die...'
        time.sleep(1)
    forward_ports=config['db_port']+":127.0.0.1:5432"
    (subprocess.Popen(['ssh','-i',rsa_key,'-o','StrictHostKeyChecking=no','-f',process_key,'-L',forward_ports,'-N'], stdout=subprocess.PIPE, close_fds=True).communicate()[0].strip())
 

# def save_object_to_file(myobject,output_file):
#     f = open(output_file,'w')
#     pickle.dump(myobject, f)
#     f.close()
# 
# def load_object_from_file(input_file):
#     return pickle.load( open( input_file, "rb" ) )


def save_peer(setup_peers_status,hostname,wl_death,rtt=-1.0,active=False):
    if not setup_peers_status is None:
        if hostname in setup_peers_status:
            setup_peers_status[hostname]['active']=active
            setup_peers_status[hostname]['dead']=wl_death
            if setup_peers_status[hostname]['rtt']>rtt and rtt>0.0:
                setup_peers_status[hostname]['rtt']=rtt
        else:
            setup_peers_status[hostname]={'rtt':rtt,'active':active,'dead':wl_death}
        
    return setup_peers_status


def get_peer_status_table():
    setup_peers_status_file=config['workload_peer_status']
    setup_peers_status={}
    nearest_peers_table={}
    if os.path.isfile(config['nearest_peers_file']):
        nearest_peers_table=load_object_from_file(config['nearest_peers_file'])
    else:
        print 'warm: empty nearest table'
        return None
    if os.path.isfile(setup_peers_status_file):
        
        try:
            setup_peers_status=load_object_from_file(setup_peers_status_file)
        except EOFError:
            os.remove(setup_peers_status_file)
            for peer in nearest_peers_table:
                setup_peers_status[peer]={'rtt':nearest_peers_table[peer],'active':False,'dead':False}  
            save_object_to_file(setup_peers_status, setup_peers_status_file)          
            return (setup_peers_status)
                
        except:
            print "unknown error in get_peer_status_table, exiting."
            sys.exit(1)        
    else:
        if config['workload_setup_peers'] == 'yes':
            for peer in nearest_peers_table:
                setup_peers_status[peer]={'rtt':nearest_peers_table[peer],'active':False,'dead':False}
            save_object_to_file(setup_peers_status, setup_peers_status_file)
    
    return setup_peers_status

def check_nearest_rtt(peer,setup_peers_status,rtt):
    if not setup_peers_status is None:    
        if peer in setup_peers_status:
            if setup_peers_status[peer]['rtt']>0.0:
                if rtt<=0.0:
                    rtt=setup_peers_status[peer]['rtt']
                elif setup_peers_status[peer]['rtt']<rtt:
                    rtt=setup_peers_status[peer]['rtt']
                else:
                    setup_peers_status[peer]['rtt']=rtt
    return (rtt,setup_peers_status)
    
###### main   
seconds=60
if len(sys.argv)==2:
    try:
        seconds=int(sys.argv[1])
        if seconds<0 or seconds>59:
            seconds=60
    except:
        print "ERROR in the sys.argv: %s" % str(sys.argv)
        seconds=60
hostname_table=get_hostname_table()
setup_peers_status=get_peer_status_table()  
        
now = time.strftime("%c")
## Display current date and time from now variable 
print ("Current time %s"  % now )

#postgres db
if config['db_tunnelling'] in ['true', 'True', '1', 't', 'y','Y', 'yes','Yes', 'yeah', 'yup', 'certainly', 'uh-huh']:
#    open_ssh_tunnel_to_master_db()
    dbconn=MyDB(config['db_name'],config['db_user'],config['db_host'],config['db_pass'],config['db_port'])    
else:
    dbconn=MyDB(config['db_name'],config['db_user'],config['db_host'],config['db_pass'])

#location=(socket.gethostname()).split('-')[0]
location=(socket.gethostname())

rrd_path_vms_prefix=config['rrd_path_vms_prefix']
rrd_path_monitor_prefix=config['rrd_path_monitor_prefix']
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
rtt_filename=config['slo_rtt_filename']
service_rtt_filename=config['slo_service_rtt_filename']
death_filename=config['slo_death_filename']
outliers_filename=config['slo_outliers_filename']

#rrd_file_prefix=config['rrd_file_prefix']

ts=time.strftime("%Y-%m-%d %H:%M:%S")

if seconds==60:
    ts=time.strftime("%Y-%m-%d %H:%M:%S")
else:
    ts="%s:%d"%(time.strftime("%Y-%m-%d %H:%M"),seconds)

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
rtt=0.0
service_rtt=0.0
wl_death=0
dead=False
outliers=0
node_target_throughput=0

number_of_workloads=0
failed_data_collection=False
print "getting nodes..."
(workload_hosts,vms,monitors,setup_peers_status,hostname_table)=get_nodes(setup_peers_status,hostname_table)
active_peers=[]
if not setup_peers_status is None:
    for peer in setup_peers_status:
        if setup_peers_status[peer]['active']:
            active_peers.append(peer)

print "number of monitored wl: %d" % len(workload_hosts)
#print workload_hosts
print "number of vms nodes: %d" % len(vms)
print "number of monitors nodes: %d" % len(monitors)
#for hostname in config['workload_hosts']:
for hostname in workload_hosts:
    dead=False
    #if node is not found it return unknown
#    path_id=get_host_path_id(hostname)
    path_id=hostname
#     if not isVMAlive(hostname):
#         continue
    rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+latency_95th_filename
    node_latency_95th=getIntValue(rrd_file)
    
    rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+latency_99th_filename
    node_latency_99th=getIntValue(rrd_file)

    rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+death_filename
    wl_death=getIntValue(rrd_file)
    if wl_death==1:
        dead=True

    rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+outliers_filename
    outliers=getIntValue(rrd_file)
    

    if (node_latency_95th>0 and node_latency_99th>0):
        #print "looking for %s" % hostname
        
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
        node_target_throughput=getIntValue(rrd_file)
        target_throughput=target_throughput+node_target_throughput
        
        rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+system_id_filename
        system_id=getIntValue(rrd_file)
        
        rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+max_latency_95th_filename
        max_latency_95th=getIntValue(rrd_file)
        
        rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+max_latency_99th_filename
        max_latency_99th=getIntValue(rrd_file)
        
        rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+max_latency_avg_filename
        max_latency_avg=getIntValue(rrd_file)

        rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+rtt_filename
        rtt=getFloatValue(rrd_file)

        rrd_file=rrd_path_workload_hosts_prefix+"/"+path_id+"/"+service_rtt_filename
        service_rtt=getFloatValue(rrd_file)

        
        number_of_workloads=number_of_workloads+1
        #check workload hostname
        (node_name,hostname_table)=check_hostname(rrd_path_workload_hosts_prefix.split('/')[-1],config['workload_user'],hostname,hostname_table)
        #print 'workload node name:%s,%s'%(hostname,node_name)
        (checked_rtt,setup_peers_status)=check_nearest_rtt(node_name, setup_peers_status, rtt)
        insert_workload_state_into_db(ts,dbconn,node_name, node_throughput, \
                                      node_violation, system_id, \
                                      node_latency_95th,node_latency_99th, \
                                      node_latency_avg,checked_rtt,location, \
                                      node_target_throughput, outliers,service_rtt)
        #def save_peer(setup_peers_status,hostname,wl_death,rtt=-1.0,active=False):
        #print (node_name in setup_peers_status)
        #print node_name
        setup_peers_status=save_peer(setup_peers_status,node_name,False,checked_rtt,True)
        if node_name in active_peers:
            active_peers.remove(node_name)
    else:
        #print "looking for %s else" % hostname
        (node_name,hostname_table)=check_hostname(rrd_path_workload_hosts_prefix.split('/')[-1],config['workload_user'],hostname, hostname_table)
        (checked_rtt,setup_peers_status)=check_nearest_rtt(node_name, setup_peers_status, -1.0)
        #def save_peer(setup_peers_status,hostname,wl_death,rtt=-1.0,active=False):
        setup_peers_status=save_peer(setup_peers_status,node_name,dead,checked_rtt)
        if node_name in active_peers:
            active_peers.remove(node_name)
    
if ((latency_95th<=0 or latency_99th<=0)) :
    failed_data_collection=True

if (number_of_workloads == 0) or failed_data_collection:
    print "workload is not running, nothing to do (latency_95th,latency_99th,number_of_workloads:%d,%d,%d)." % (latency_95th,latency_99th,number_of_workloads)
    print '[%s] Done.' % ts
    sys.exit(0)

print "number of active wl: %d" % number_of_workloads
    
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
        if is_it_an_invalid_rrd_file(db_key):
            continue
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
    (vm_hostname,hostname_table)=get_hostname(rrd_path_vms_prefix.split('/')[-1], config['guest_vm_sys_user'],node,hostname_table)
    insert_vm_stat_into_db(ts,vm_hostname,dbconn,keys,isFailed(config, fault_flag,workload_hosts),values,location)
    number_of_vms = number_of_vms + 1

#save slo status
insert_slo_state_into_db(ts, dbconn, throughput, violation, \
                         target_throughput,system_id, \
                         number_of_vms,latency_95th,latency_99th,latency_avg, \
                         max_latency_95th,max_latency_99th,max_latency_avg, \
                         location,number_of_workloads)


#for hostname in config['vms']:
for node in monitors:
    #if node is not found it return unknown
#    path_id=get_host_path_id(hostname)
    path_id=node
    stat={}
    list_of_files = (sorted(glob.glob(rrd_path_monitor_prefix+"/"+path_id+"/*.rrd")))
    keys=""
    values=""
    #check fault injection
#     alive=True
    for filename in list_of_files:
#         if not isVMAlive(hostname):
#             alive=False
#             break
        db_key= ( (filename).split('/')[-1] ).split('.')[0]
        if is_it_an_invalid_rrd_file(db_key):
            continue
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
    
    insert_monitor_stat_into_db(ts,node,dbconn,keys,values,location)



print dbconn.getDebugMess()

for peer in active_peers:
    
    
#    print peer
#     rtt=setup_peers_status[peer]['rtt']
#     #def save_peer(setup_peers_status,hostname,wl_death,rtt=-1.0,active=False):
#     save_peer(setup_peers_status, peer, False,rtt)
# config['rrd_path_workload_hosts_prefix']
# config['slo_throughput_filename']    
# def isPeerAlive(path_to_rrd,rrd_filename,peer):
#     path_id=get_host_path_id(peer)    
#     try:
#         rrd_file=path_to_rrd+"/"+path_id+"/"+rrd_filename
#         return ((long(time.time())-(rrdtool.info(rrd_file)["last_update"]))<=ALIVE_TIME)
#     except:
#         return False

#config['rrd_path_workload_hosts_prefix']
#config['slo_throughput_filename']

    
    if isPeerDead(config['rrd_path_workload_hosts_prefix'], config['slo_throughput_filename'], peer):
        setup_peers_status[peer]['active']=False
        setup_peers_status[peer]['dead']=True
        
#     else:
#         if isVMDead(peer):
#             setup_peers_status[peer]['active']=False
#             setup_peers_status[peer]['dead']=True
    
    
save_object_to_file(setup_peers_status,config['workload_peer_status'])
save_object_to_file(hostname_table, hostname_table_file)
    
#if config['db_tunnelling'] in ['true', 'True', '1', 't', 'y','Y', 'yes','Yes', 'yeah', 'yup', 'certainly', 'uh-huh']:
#    close_ssh_tunnel_to_master_db()
print '[%s] Done.' % ts

sys.exit(dbconn.get_status())


