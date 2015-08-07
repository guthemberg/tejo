import pickle,sys,socket,subprocess,os,random
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

def load_object_from_file(input_file):
    return pickle.load( open( input_file, "rb" ) )

def save_object_to_file(myobject,output_file):
    f = open(output_file,'w')
    pickle.dump(myobject, f)
    f.close()
    
    
if __name__ == '__main__':
    print "[%s]:getting rtt..."%(str(datetime.now()))    
    tejo_config=ConfigObj(TEJO_CONF_FILE)
    path_to_yanoama='/home/'+tejo_config['workload_user']+'/yanoama'
    current_rtt=0.0
    if os.path.isfile(tejo_config['workload_rtt']):
        current_rtt=float(load_object_from_file(tejo_config['workload_rtt']))
    
    rtt=getRTT_SSH(tejo_config['workload_target'], path_to_yanoama)
    
    if rtt>0.0:
        if current_rtt>0.0:
            if rtt<current_rtt:
                save_object_to_file(rtt, tejo_config['workload_rtt'])
        else:
            save_object_to_file(rtt, tejo_config['workload_rtt'])
            
    sys.exit(0)

            
        
