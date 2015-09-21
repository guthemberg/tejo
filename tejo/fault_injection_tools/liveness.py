import os
import socket
import rrdtool
import glob
import sys
from configobj import ConfigObj
import time,subprocess
import pickle
from urllib2 import urlopen
import xmltodict

#db api available in home_dir



#db api available in home_dir
conf_file = "/etc/tejo.conf"
config=ConfigObj(conf_file)
sys.path.append(config['home_dir'])
ALIVE_TIME=int(config['alive_time'])
DEATH_TIME=int(config['time_to_vm_death'])



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




def get_hostname_table():
    hostname_table={}
    if os.path.isfile(hostname_table_file):
        hostname_table=load_object_from_file(hostname_table_file)
    else:
        save_object_to_file(hostname_table, hostname_table_file)
    return hostname_table



def check_hostname(cluster,username,name,hostname_table):
    try:
        int(name.split('.')[-1])
        return (get_hostname(cluster, username,name,hostname_table))
    except:
        ##this means that the hostname is ok!!!
        return (name,hostname_table)

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


def get_mongodb_all_primary_replicas_vms(vms):
    primary_replicas=""
    for hostname in vms:
        try:
            if (int(rrdtool.info(config['rrd_path_vms_prefix']+"/"+hostname+"/"+config['vm_mongodb_is_primary_filename'])['ds[sum].last_ds'])==1) and (isVMAlive(hostname)):
                primary_replicas=primary_replicas+hostname+","
        except:
            pass
    if len(primary_replicas)>0:
        return primary_replicas[:-1]
    return primary_replicas

def get_mongodb_all_secondary_replicas_vms(vms):
    secondary_replicas=""
    for hostname in vms:
        try:
            if (int(rrdtool.info(config['rrd_path_vms_prefix']+"/"+hostname+"/"+config['vm_mongodb_is_primary_filename'])['ds[sum].last_ds'])==0) and (isVMAlive(hostname)):
                secondary_replicas=secondary_replicas+hostname+","
        except:
            pass
    if len(secondary_replicas)>0:
        return secondary_replicas[:-1]
    return secondary_replicas


#### main
hostname_table=get_hostname_table()
setup_peers_status=get_peer_status_table()  


(workload_hosts,vms,monitors,setup_peers_status,hostname_table)=get_nodes(setup_peers_status,hostname_table)

if len(sys.argv)==1:
    sys.stdout.write(get_mongodb_all_primary_replicas_vms(vms))
elif len(sys.argv)>1:
    if sys.argv[1] != 'secondary':
        sys.stdout.write(get_mongodb_all_primary_replicas_vms(vms))
    else:
        sys.stdout.write(get_mongodb_all_secondary_replicas_vms(vms))
        
