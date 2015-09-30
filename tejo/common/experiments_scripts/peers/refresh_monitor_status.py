import pickle,sys,socket,subprocess,os,git,random
from pymongo import MongoClient
import datetime
from time import time
#from planetlab import Monitor
from configobj import ConfigObj



PLE_CONF_FILE='/etc/ple.conf'
TEJO_CONF_FILE='/etc/tejo.conf'

#db api available in home_dir
config=ConfigObj(TEJO_CONF_FILE)
sys.path.append(config['home_dir'])

#available in home_dir
from tejo.common.db.postgres.database import MyDB


def clone_git_repository(uri_repository):
    subprocess.Popen(['git','clone',uri_repository], stdout=subprocess.PIPE, close_fds=True).communicate()[0].strip()

def getRTT_TCP(hostname, yanoama_root,port=22):
    try:
        script_to_run=yanoama_root+'/yanoama/monitoring/get_rtt_tcp.sh'
        rtt=float(subprocess.Popen(['sh',script_to_run,hostname,str(port)], stdout=subprocess.PIPE, close_fds=True).communicate()[0].strip())
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
    list_of_peers=list(status.find({'peer': peer}))
    if len(list_of_peers)!=1:
        print "WARNING: inconsistent number of oids (list size: %d, content: %s, peer:%s), leaving." % (len(list_of_peers),str(list_of_peers),peer)
    else:            
        object_id=list_of_peers[0]['_id']
        status.update({'_id':object_id},{'$set':{'monitor':monitor}})
        status.update({'_id':object_id},{'$set':{'monitor_rtt':rtt}})
        status.update({'_id':object_id},{'$set':{'monitors':monitors}})
    #    status.update({'peer':peer},{'$set':{'monitor':monitor}}, upsert=False,check_keys=False)
    #    status.update({'peer':peer},{'$set':{'monitor_rtt':rtt}}, upsert=False,check_keys=False)
    #    status.update({'peer':peer},{'$set':{'monitors':monitors}}, upsert=False,check_keys=False#)
    c.close()    

def add_peer(peer, monitor, rtt):
    host=(socket.gethostname())
    c = MongoClient(host, 27017)
    db=c.tejo
    status=db.status
    list_of_peers=list(status.find({'peer': peer}))
    if len(list_of_peers)==0:
        monitors={monitor.split('.')[0]:rtt}
        status.insert({'peer':peer,'monitor':monitor,'target':monitor,'monitor_rtt':rtt,'target_rtt':rtt,'monitors':monitors,'active':False},check_keys=False)
    else:
        print "addition Failed"
    c.close()    

def get_list_of_monitors():
    host=(socket.gethostname())
    c = MongoClient(host, 27017)
    db=c.azure
    monitors=db.monitors
    list_of_monitors=list(monitors.find())
    c.close()    
    return list_of_monitors


def add_monitor(monitor, crowd=-1,score=-1):
    host=(socket.gethostname())
    c = MongoClient(host, 27017)
    db=c.azure
    monitors=db.monitors
    monitors.insert({'monitor':monitor,'ts':time(),'score':score,'crowd':crowd},check_keys=False)
    c.close()    

def update_monitor(monitor,crowd,score):
    host=(socket.gethostname())
    c = MongoClient(host, 27017)
    db=c.azure
    status=db.monitors
    list_of_monitors=list(status.find({'monitor': monitor}))
    if len(list_of_monitors)!=1:
        print "WARNING: inconsistent number of oids (list size: %d, content: %s, monitor:%s), leaving." % (len(list_of_monitors),str(list_of_monitors),monitor)
    else:            
        object_id=list_of_monitors[0]['_id']
        status.update({'_id':object_id},{'$set':{'monitor':monitor}})
        status.update({'_id':object_id},{'$set':{'score':score}})
        status.update({'_id':object_id},{'$set':{'crowd':crowd}})
        status.update({'_id':object_id},{'$set':{'ts':time()}})
    #    status.update({'peer':peer},{'$set':{'monitor':monitor}}, upsert=False,check_keys=False)
    #    status.update({'peer':peer},{'$set':{'monitor_rtt':rtt}}, upsert=False,check_keys=False)
    #    status.update({'peer':peer},{'$set':{'monitors':monitors}}, upsert=False,check_keys=False#)
    c.close()    


def remove_monitor(monitor):
    host=(socket.gethostname())
    c = MongoClient(host, 27017)
    db=c.azure
    monitors=db.monitors
    monitors.remove({'monitor':monitor})
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

def get_local_monitor_state(dbconn,target_ts=None,max_ts=None):
    crowd=-1
    score=-1
    #past minute
    now=datetime.datetime.now()
    last_minute=now-datetime.timedelta(minutes=1)
    if target_ts is None:
        target_ts=("%s:%s")%(last_minute.strftime("%Y-%m-%d %H:%M"),'00')
    if max_ts is None:
        max_ts="%s:%s"%(now.strftime("%Y-%m-%d %H:%M"),'00')
    select_result=dbconn.getSelect(("SELECT ts,outliers from workload where ts>='%s' and ts<'%s'")%(target_ts,max_ts))
    current_time=''
    for line in select_result:
        current_time_candidate=line[0].strftime("%Y-%m-%d %H:%M:%S")
        if len(current_time)==0 and len(current_time_candidate)>0:
            score=0
            crowd=0
            current_time=line[0].strftime("%Y-%m-%d %H:%M:%S")
            
        if current_time == line[0].strftime("%Y-%m-%d %H:%M:%S"):
            score_to_be_added=int(line[1])
            if score_to_be_added>0:
                score=score+score_to_be_added
            crowd=crowd+1
            
    return (crowd,score)

if __name__ == '__main__':
    
    print "[%s]:update membership..."%(str(datetime.datetime.now()))
    tejo_config=ConfigObj(TEJO_CONF_FILE)
    dbconn=MyDB(tejo_config['db_name'],tejo_config['db_user'],tejo_config['db_host'],tejo_config['db_pass'])
    monitors_list_azure=get_list_of_monitors()
    myself=socket.gethostname()
    perform_update=False
    for monitor in monitors_list_azure:
        #check if peer is alive
        if monitor['monitor'] == myself:
            perform_update=True
    (crowd,score)=get_local_monitor_state(dbconn)
    if perform_update:
        update_monitor(myself, crowd, score)
    else:
        add_monitor(monitor, crowd, score)
    print "[%s]:done."%(str(datetime.datetime.now())) 
#    print get_list_of_monitors()   
    sys.exit(0)
