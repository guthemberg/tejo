import pickle,sys,socket,subprocess,os,git
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

def update_peer_server(peer, server, rtt):
    host=(socket.gethostname())
    c = MongoClient(host, 27017)
    db=c.tejo
    status=db.status
    status.update({'client':peer},{'$set':{'server':server}}, upsert=False)
    status.update({'client':peer},{'$set':{'rtt':rtt}}, upsert=False)
    c.close()    

def add_peer(peer, server, rtt):
    host=(socket.gethostname())
    c = MongoClient(host, 27017)
    db=c.tejo
    status=db.status
    status.insert({'client':peer,'server':server,'rtt':rtt})
    c.close()    

def remove_peer(peer):
    host=(socket.gethostname())
    c = MongoClient(host, 27017)
    db=c.tejo
    status=db.status
    status.remove({'client':peer})
    c.close()    

def save_workload_list(workload_list,output_file='/home/user/workload_list.pck'):
    dic_node_file=output_file
    f = open(dic_node_file,'w')
    pickle.dump(workload_list, f)
    f.close()

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

    #steps
    #1) get the list of ple peers
    peers=get_list_of_peers()
    existing_peers={}
    for peer in peers:
        existing_peers[peer['client']]={'server':peer['server'],'rtt':peer['rtt']}
    #2) get the list of ple nodes
    config=ConfigObj(PLE_CONF_FILE)
    ple = PlanetLabAPI(config['username'],config['password'],config['host'])
    ple_nodes=ple.getSliceHostnames(config['slice'])
    #3) compute rtt
    number_of_nodes=len(ple_nodes)
    measured_nodes=1
    server=(socket.gethostname())
    worload_peers={}
    for node in ple_nodes:
        rtt=getRTT_SSH(node,path_to_yanoama)
        if rtt > 0.0:
            action='none'
            if node not in existing_peers:
                action='added'
                add_peer(node, server, rtt)
                existing_peers[node]={'server':server,'rtt':rtt}
            elif rtt<existing_peers[node]['rtt']:
                existing_peers[node]['server']=server
                update_peer_server(node, server, rtt)
                action='updated'
            if existing_peers[node]['server']==server:
                worload_peers[node]=rtt
            del existing_peers[node]
            print '(%d/%d)%s:%.4f [%s]'%(measured_nodes,number_of_nodes,node,rtt,action)
        else:
            print '(%d/%d)failed for %s'%(measured_nodes,number_of_nodes,node)
        measured_nodes=measured_nodes+1
    output_file=tejo_config['workload_list_file']
    save_workload_list(worload_peers, output_file)
    #4) clean up db
    number_of_nodes=len(existing_peers)
    peers_names=existing_peers.keys()
    measured_nodes=1
    for peer in peers_names:
        remove_peer(peer)
        print '(%d/%d)%s [%s]'%(measured_nodes,number_of_nodes,peer,'removed')
        measured_nodes=measured_nodes+1

    print "number of members: %d" % len(worload_peers)
    print "[%s]:done."%(str(datetime.now()))  
    sys.exit(0)
    
