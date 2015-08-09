import pickle,sys,socket,subprocess,os,random
from datetime import datetime
from time import mktime,sleep
#from planetlab import Monitor
from configobj import ConfigObj


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

def is_file_new(input_file,last_ts,delta=60):    
    if (int(os.path.getmtime(input_file))-last_time_file)>delta:
        return True
    return False
    
def get_smaller_value(lista,target):
    for value in sorted(lista, reverse=True):
        if value < target:
            return value
    return target

if __name__ == '__main__':

    tejo_config=ConfigObj(TEJO_CONF_FILE)
    throughput_values=[50,100,200]
    current_throughput=int(tejo_config['mongo_default_throughput'])
    system_id=int(tejo_config['system_id'])
    rtt_list_file='/tmp/peer_rtt_list.pck'
    last_time_file='/tmp/peer_rtt_list_last_ts.pck'
    rtt_list=[]
    if os.path.isfile(rtt_list_file):
        rtt_list=load_object_from_file(rtt_list_file)
        
    last_time=int(time.time())
    if os.path.isfile(last_time_file):
        last_time=load_object_from_file(last_time_file)
        
    save_object_to_file(int(time.time()), last_time_file)
    
    
    rtt_file=tejo_config['workload_rtt']
    rtt=0
    if os.path.isfile(rtt_file):
        rtt=int(load_object_from_file(rtt_file))
        
    latency_99th_file='/tmp/slo_latency_99th.txt'
    
    if rtt>0:
        if os.path.isfile(latency_99th_file):
            if is_file_new(latency_99th_file,last_time):
                current_latency=0
                try:
                    current_latency=int(''.join(open(latency_99th_file, 'r').readlines()).strip())
                except :
                    current_latency=int(0)
                    
                if current_latency>0:
                    if current_latency>rtt:
                        rtt_list.append(current_latency-rtt)

    target_len=10
    target_throughput=get_smaller_value(throughput_values, current_throughput)
    if len(rtt_list)>=target_rtt and target_throughput<current_throughput:
        target_rtt=100
        outliers=0
        for sample in rtt_list:
            if sample>target_rtt:
                outliers=outliers+1
        
        if outliers >= (target_len/2):
            if system_id==0:
                sed_cmd="\"s|mongo_default_throughput="+current_throughput+"|mongo_default_throughput="+target_throughput+"|g\""
                subprocess.Popen(["sudo","sed","-i",sed_cmd,'/etc/tejo.conf'], stdout=subprocess.PIPE, close_fds=True).communicate()[0].strip()
                stop_script="/home/"+tejo_config['workload_user']+"/tejo/tejo/common/experiments_scripts/ycsb/stop.sh" 
                subprocess.Popen(["/bin/sh",stop_script], stdout=subprocess.PIPE, close_fds=True).communicate()[0].strip()            
                subprocess.Popen(["touch", tejo_config['mongo_active_wl_file']], stdout=subprocess.PIPE, close_fds=True).communicate()[0].strip()
                check_script="/home/"+tejo_config['workload_user']+"/tejo/contrib/pl/check_workload.sh" 
                subprocess.Popen(["/bin/sh",check_script], stdout=subprocess.PIPE, close_fds=True).communicate()[0].strip()
            save_object_to_file([], rtt_list_file)               
        else:
            save_object_to_file(rtt_list[1:], rtt_list_file)               

        
    else:
        save_object_to_file(rtt_list, rtt_list_file) 
    
    sys.exit(0)              
        
        
    
    
    print "last modified: %s" % time.ctime(os.path.getmtime(tejo_config['workload_rtt']))
    print "created: %s" % time.ctime(os.path.getctime(file))