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
    if not os.path.isdir(path_to_yanoama):
        print 'getting yanoama...'
        r=git.Repo.clone_from("https://github.com/guthemberg/yanoama.git",path_to_yanoama)
        print 'got it.'
    ple_lib_path=path_to_yanoama+'/yanoama/planetlab'
    sys.path.append(ple_lib_path)
    
    from planetlab import PlanetLabAPI
    config=ConfigObj(PLE_CONF_FILE)
    ple = PlanetLabAPI(config['username'],config['password'],config['host'])
    ple_nodes=ple.getSliceHostnames(config['slice'])
    #3) compute rtt
    number_of_nodes=len(ple_nodes)
#    print ple_nodes
    
    print "current number of ple nodes: %d" % number_of_nodes

    #steps
    #1) get the list of ple peers
    peers=get_list_of_peers()
#    print "current number of peers: %d" % len(peers)
    monitors_list=[]
    all_peers_list={}
    nearest_peers_list={}
    monitor=(socket.gethostname())
    peers_to_be_removed=[]
    new_peers={}
    peer_to_update={}
#    worload_peers={}

    operation_tokens=20
    remaining_operation_tokens=operation_tokens
    #1.1) 
    
    
    for peer in peers:
        if remaining_operation_tokens > 0 and (not(peer['peer'] in ple_nodes)):
            print "CHECKING: %s: %s" % (peer['peer'],str((not(peer['peer'] in ple_nodes))))
            print ple_nodes
            peers_to_be_removed.append(peer['peer'])
            remaining_operation_tokens=remaining_operation_tokens-1
        elif peer['peer'] in ple_nodes:
            ple_nodes.remove(peer['peer'])
            all_peers_list[peer['peer']]={'monitor':peer['monitor'],'monitor_rtt':peer['monitor_rtt'],'target':peer['target'],'target_rtt':peer['target_rtt'],'monitors':peer['monitors'],'active':peer['active']}
            if peer['monitor'] not in monitors_list:
                monitors_list.append(peer['monitor'])
            if peer['monitor'] == monitor:
                nearest_peers_list[peer['peer']]=peer['monitor_rtt']

    print "current number of peers: %d " % len(all_peers_list)
#    print all_peers_list
    save_object_to_file(all_peers_list, tejo_config['all_peers_file'])
    print "current monitors list size: %d " % len(monitors_list)
#    print monitors_list                
    save_object_to_file(monitors_list, tejo_config['monitors_list_file'])
    print "current nearest peers list size: %d " % len(nearest_peers_list)
#    print nearest_peers_list                
    save_object_to_file(nearest_peers_list, tejo_config['nearest_peers_file'])
                
    #computing new nodes
    while remaining_operation_tokens > 0 and len(ple_nodes) > 0:
        node=ple_nodes[0]
        rtt=getRTT_SSH(node,path_to_yanoama)
        if rtt>0:
            new_peers[node]=rtt
            remaining_operation_tokens=remaining_operation_tokens-1
        ple_nodes.remove(node)
        
    #updating existing nodes
    while remaining_operation_tokens > 0 and len(all_peers_list) > 0:
        peer=all_peers_list.keys()[random.randrange(0,len(all_peers_list.keys()))]
        rtt=getRTT_SSH(peer,path_to_yanoama)
        if rtt<all_peers_list[peer]['monitor_rtt'] and rtt>0:
            monitors=all_peers_list[peer]['monitors']
            monitors[monitor.split('.')[0]]=rtt
            peer_to_update[peer]={'monitor_rtt':rtt,'monitors':monitors}
            remaining_operation_tokens=remaining_operation_tokens-1
        del all_peers_list[peer]
    
    #performing all operations in order
    
    measured_nodes=0
    for peer in peers_to_be_removed:
        remove_peer(peer)
        measured_nodes=measured_nodes+1
        print '(%d/%d)%s [REMOVED]'%(measured_nodes,operation_tokens,peer)
        
    for peer in new_peers:
        add_peer(peer, monitor, new_peers[peer])
        measured_nodes=measured_nodes+1
        print '(%d/%d)%s:%.4f [ADDED]'%(measured_nodes,operation_tokens,peer,new_peers[peer])
        
    for peer in peer_to_update:
        update_peer_monitor(peer, monitor, peer_to_update[peer]['monitor_rtt'], peer_to_update[peer]['monitors'])
        measured_nodes=measured_nodes+1
        print '(%d/%d)%s:%.4f (rtt) , %d (number of monitors) [UPDATED]'%(measured_nodes,operation_tokens,peer,peer_to_update[peer],len(peer_to_update[peer]['monitors']))

    print "[%s]:done."%(str(datetime.now()))  
    sys.exit(0)
        
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
