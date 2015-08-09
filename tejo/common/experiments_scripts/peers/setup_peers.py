import pickle,sys,socket,subprocess,os,git,random
from pymongo import MongoClient
from datetime import datetime
from time import mktime,sleep
#from planetlab import Monitor
from configobj import ConfigObj


try:
    import json
except ImportError:
    import simplejson as json

PLE_CONF_FILE='/etc/ple.conf'
TEJO_CONF_FILE='/etc/tejo.conf'



def clone_git_repository(uri_repository):
    subprocess.Popen(['git','clone',uri_repository], stdout=subprocess.PIPE, close_fds=True).communicate()[0].strip()

def getRTT_SSH(hostname, yanoama_root):
    try:
        script_to_run=yanoama_root+'/yanoama/monitoring/get_rtt_ssh.sh'
        rtt=float(subprocess.Popen(['sh',script_to_run,hostname], stdout=subprocess.PIPE, close_fds=True).communicate()[0].strip())
        if rtt>0.0:
            return rtt
        else:
            return -1
    except:
        return -1

#this returns a list of peers [ {k1:e1,...},...]
#each entry the the following structure:
#{u'rtt': 11.0, u'_id': ObjectId('55b955cf465cba3f890fa36e'), 
#  u'server': u'us-monitor-001.cloudapp.net', 
#  u'client': u'planetlab1.cs.ucla.edu'}
def get_list_of_peers():
    host=(socket.gethostname())
    c = MongoClient(host, 27017)
    db=c.tejo
    status=db.status
    list_of_peers=list(status.find())
    c.close()    
    return list_of_peers

def update_peer_monitor(peer, monitor, rtt,monitors):
    host=(socket.gethostname())
    c = MongoClient(host, 27017)
    db=c.tejo
    status=db.status
    status.update({'peer':peer},{'$set':{'monitor':monitor}}, upsert=False,check_keys=False)
    status.update({'peer':peer},{'$set':{'monitor_rtt':rtt}}, upsert=False,check_keys=False)
    status.update({'peer':peer},{'$set':{'monitors':monitors}}, upsert=False,check_keys=False)
    c.close()    

def add_peer(peer, monitor, rtt):
    host=(socket.gethostname())
    c = MongoClient(host, 27017)
    db=c.tejo
    status=db.status
    monitors={monitor.split('.')[0]:rtt}
    status.insert({'peer':peer,'monitor':monitor,'target':monitor,'monitor_rtt':rtt,'target_rtt':rtt,'monitors':monitors,'active':False},check_keys=False)
    c.close()    

def remove_peer(peer):
    host=(socket.gethostname())
    c = MongoClient(host, 27017)
    db=c.tejo
    status=db.status
    status.remove({'peer':peer})
    c.close()    

def save_workload_list(workload_list,output_file='/home/user/workload_list.pck'):
    dic_node_file=output_file
    f = open(dic_node_file,'w')
    pickle.dump(workload_list, f)
    f.close()

def save_object_to_file(myobject,output_file):
    f = open(output_file,'w')
    pickle.dump(myobject, f)
    f.close()

def load_object_from_file(input_file):
    return pickle.load( open( input_file, "rb" ) )


if __name__ == '__main__':
    print "[%s]:update membership..."%(str(datetime.now()))    
    tejo_config=ConfigObj(TEJO_CONF_FILE)
    path_to_yanoama=tejo_config['root_dir']+'/yanoama'
    setup_peers_status_file=tejo_config['root_dir']+'/peers_tatus_table.pck'
    setup_peers_status={}
    nearest_peers_table={}
    if os.path.isfile(tejo_config['nearest_peers_file']):
        nearest_peers_table=load_object_from_file(tejo_config['nearest_peers_file'])
    if os.path.isfile(setup_peers_status_file):
        setup_peers_status=load_object_from_file(setup_peers_status_file)
        #cleanup list
        for peer in setup_peers_status:
            if not peer in nearest_peers_table:
                del setup_peers_status[peer] 
        for peer in nearest_peers_table:
             if not peer in setup_peers_status:
                 setup_peers_status[peer]={'rtt':nearest_peers_table[peer],'active':False}
    else:
        for peer in nearest_peers_table:
            setup_peers_status[peer]={'rtt':nearest_peers_table[peer],'active':False}
     
        
    #getting non setuped nodes
    candidates=[]
    for peer in setup_peers_status:
        if not setup_peers_status[peer]['active']:
            candidates.append(peer)
            
    
    if len(sys.argv)==2:
        peer_to_save=sys.argv[1]
        setup_peers_status[peer_to_save]['active']=True
        save_object_to_file(setup_peers_status, setup_peers_status_file)
        sys.exit(0)

    #to setup
    
    if len(candidates)>0:
        peer_to_setup=candidates[random.randrange(0,len(candidates))]
        sys.stdout.write(peer_to_setup)
        sys.exit(0)
        
    sys.exit(1)
    
#         
#     script_path=tejo_config['home_dir']+'/contrib/pl/setup.sh'
#     script_output = subprocess.Popen(['/bin/sh',script_path,peer_to_setup], stdout=subprocess.PIPE, close_fds=True).communicate()[0]
#     script_path='/home/'+tejo_config['workload_user']+'/tejo/tejo/common/experiments_scripts/peers/check_running_peer.sh'
#     key=tejo_config['root_dir']+"/.ssh/id_rsa_cloud"
#     ssh_args=tejo_config['workload_user']+"@"+peer_to_setup    
#     script_output = subprocess.Popen(['ssh','-i', key, "-o", "StrictHostKeyChecking=no", "-t", ssh_args,'/bin/sh',script_path], stdout=subprocess.PIPE, close_fds=True).communicate()[0].strip()
#     print "script output: (%s)"%script_output
#     if script_output=='ok':
#         print '%s: ok!' % peer_to_setup
#         setup_peers_status[peer_to_setup]['active']=True
#         save_object_to_file(setup_peers_status, setup_peers_status_file)
#     else:
#         print '%s: failed!' % peer_to_setup
# 
# 
# 
#     print "[%s]:done."%(str(datetime.now()))  
#     sys.exit(0)
        
#         
# #    save_workload_list(worload_peers, tejo_config['workload_list_file'])
#         
#     #2) get the list of ple nodes
#     
#     ###get monitor list
#     
#     
#     max_updates=10
#     steps=max_updates
#     
#     peers_to_remove=[]
#     while max_updates>0 and len(ple_nodes)>0:
#         node=ple_nodes[random.randrange(0,len(ple_nodes))]
#         ple_nodes.remove(node)
#         
#         rtt=getRTT_SSH(node,path_to_yanoama)
#         if rtt > 0.0:
#             action='none'
#             if node not in all_peers_list:
#                 action='added'
#                 add_peer(node, monitor, rtt)
#                 all_peers_list[node]={'monitor':monitor,'rtt':rtt}
#             elif rtt<all_peers_list[node]['rtt']:
#                 print "updating %s (%s,%.4f)" % (node, all_peers_list[node]['monitor'], all_peers_list[node]['rtt'])
#                 all_peers_list[node]['monitor']=monitor
#                 update_peer_monitor(node, monitor, rtt)
#                 action='updated'
#             else:
#                 rtt=all_peers_list[node]['rtt']
#                 
#             if all_peers_list[node]['monitor']==monitor:
#                 nearest_peers_list[node]=rtt
#             else:
#                 monitor=all_peers_list[node]['monitor']
#                 
#                 
#             all_peers_list={'rtt':rtt,'monitor':monitor}
# #            del existing_peers[node]
#             print '(%d/%d)%s:%.4f [%s]'%(measured_nodes,steps,node,rtt,action)
#         else:
#             peers_to_remove.append(node)
#             print '(%d/%d)failed for %s'%(measured_nodes,steps,node)
#         measured_nodes=measured_nodes+1
#         
#         max_updates=max_updates-1
#     
# #     for node in ple_nodes:
# #         rtt=getRTT_SSH(node,path_to_yanoama)
# #         if rtt > 0.0:
# #             action='none'
# #             if node not in existing_peers:
# #                 action='added'
# #                 add_peer(node, server, rtt)
# #                 existing_peers[node]={'server':server,'rtt':rtt}
# #             elif rtt<existing_peers[node]['rtt']:
# #                 existing_peers[node]['server']=server
# #                 update_peer_server(node, server, rtt)
# #                 action='updated'
# #             else:
# #                 rtt=existing_peers[node]['rtt']
# #                 
# #             if existing_peers[node]['server']==server:
# #                 nearest_peers_list[node]=rtt
# #             else:
# #                 server=existing_peers[node]['server']
# #                 
# #             if existing_peers[node]['server'] not in monitors_list:
# #                 monitors_list.append(existing_peers[node]['server'])
# #                 
# #             all_peers_list={'rtt':rtt,'server':server}
# #             del existing_peers[node]
# #             print '(%d/%d)%s:%.4f [%s]'%(measured_nodes,number_of_nodes,node,rtt,action)
# #         else:
# #             print '(%d/%d)failed for %s'%(measured_nodes,number_of_nodes,node)
# #         measured_nodes=measured_nodes+1
#     
#     #4) clean up db
#     number_of_nodes=len(peers_to_remove)
#     peers_names=peers_to_remove
#     measured_nodes=1
#     for peer in peers_names:
#         remove_peer(peer)
#         print '(%d/%d)%s [%s]'%(measured_nodes,number_of_nodes,peer,'removed')
#         measured_nodes=measured_nodes+1
# 
#     print "number of members: %d" % len(nearest_peers_list)
#     print "[%s]:done."%(str(datetime.now()))  
#     sys.exit(0)
#     
