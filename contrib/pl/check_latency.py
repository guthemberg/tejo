import pickle,sys,socket,subprocess,os,random
from datetime import datetime
from time import mktime,sleep
import time
#from planetlab import Monitor
from configobj import ConfigObj


PLE_CONF_FILE='/etc/ple.conf'
TEJO_CONF_FILE='/etc/tejo.conf'



def getRTT_TCP(hostname, yanoama_root,port=22):
    try:
        script_to_run=yanoama_root+'/yanoama/monitoring/get_rtt_tcp.sh'
        rtt=float(subprocess.Popen(['sh',script_to_run,hostname,port], stdout=subprocess.PIPE, close_fds=True).communicate()[0].strip())
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

def is_file_new(input_file,last_ts,delta=30):    
    if (int(os.path.getmtime(input_file))-last_ts)>delta:
        return True
    return False
    
def get_smaller_value(lista,target):
    for value in sorted(lista, reverse=True):
        if value < target:
            return value
    return target

def get_bigger_value(lista,target):
    for value in sorted(lista):
        if value > target:
            return value
    return target

##it returns:
##1 to increase
##0 to keep
##-1 to reduce
def check_rtt_values(rtt_list,target_rtt,downgrade_length,upgrade_length,outliers_file):
    base_rate=2
    outliers=0
    if upgrade_length>=downgrade_length and len(rtt_list)>=downgrade_length and downgrade_length>=base_rate:
        for sample in rtt_list[-(downgrade_length):]:
            if sample>target_rtt:
                outliers=outliers+1
        if outliers>(int(downgrade_length/base_rate)):
            save_object_to_file(outliers, outliers_file)
            return 'decrease'
        #extended search to upgrade
        if len(rtt_list)>=upgrade_length:
            for sample in rtt_list[-(upgrade_length):-(downgrade_length)]:
                if sample>target_rtt:
                    outliers=outliers+1
            if outliers==0:
                save_object_to_file(outliers, outliers_file)
                return 'increase'
    elif len(rtt_list) > 0:
        for sample in rtt_list:
            if sample>target_rtt:
                outliers=outliers+1
        save_object_to_file(outliers, outliers_file)
        return 'ok'
    save_object_to_file(outliers, outliers_file)
    return 'ok'
 

if __name__ == '__main__':

    tejo_config=ConfigObj(TEJO_CONF_FILE)
    throughput_values=map(int,tejo_config['workload_target_rates'])
    current_throughput=int(tejo_config['workload_throughput'])
    system_id=int(tejo_config['system_id'])
    rtt_list_file='/tmp/peer_rtt_list.pck'
    last_time_file='/tmp/peer_rtt_list_last_ts.pck'
    rtt_list=[]
    if os.path.isfile(rtt_list_file):
        rtt_list=load_object_from_file(rtt_list_file)
    downgrade_length=10
    upgrade_length=20
    target_rtt=100


    if len(sys.argv)==4:
        peer_is_dead=int(sys.argv[1])
        if peer_is_dead==1:
            save_object_to_file([], rtt_list_file)
            save_object_to_file(int(time.time()), last_time_file)
            save_object_to_file(True,tejo_config['workload_death_file'])
            sys.exit(1)
            
        erase_rtt_list_flag=int(sys.argv[2])
        if erase_rtt_list_flag == 1:
            save_object_to_file([], rtt_list_file)
        else:
            rtt_list.append(int(sys.argv[3]))
            if len(rtt_list)<=upgrade_length:
                save_object_to_file(rtt_list, rtt_list_file)
            else:
                save_object_to_file(rtt_list[1:], rtt_list_file)
        save_object_to_file(int(time.time()), last_time_file)

        sys.exit(0)

        
    last_time=int(time.time())
    if os.path.isfile(last_time_file):
        last_time=load_object_from_file(last_time_file)
    else:
        save_object_to_file(int(time.time()), last_time_file)
        
    #check liveness of the workload
    ##timeout is 24 hour (60*60*24 in seconds)
    to_kill=0
    if (last_time-int(time.time()))>(60*60*24):
        to_kill=1
        sys.stdout.write("%s %d %d %d %d"%('whatever',0,0,0,to_kill))
        sys.exit(0)

            
    
    rtt_file=tejo_config['workload_rtt']
    rtt=0
    if os.path.isfile(rtt_file):
        rtt=int(load_object_from_file(rtt_file))
    else:
        sys.exit(1)

        
    latency_99th_file='/tmp/slo_latency_99th.txt'
    
    new_rtt=0
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
                        new_rtt=current_latency-rtt
                        rtt_list.append(new_rtt)
                    else:
                        sys.exit(1)
                else:
                    sys.exit(1)
            else:
                sys.exit(1)

        else:
            sys.exit(1)


    action=check_rtt_values(rtt_list, target_rtt, downgrade_length, upgrade_length,tejo_config['workload_outliers_file'])
    

    #to setup
    #when len(sys.argv)==1
    smaller_target_throughput=get_smaller_value(throughput_values, current_throughput)
    bigger_target_throughput=get_bigger_value(throughput_values, current_throughput)
    sys.stdout.write("%s %d %d %d %d"%(action,smaller_target_throughput,bigger_target_throughput,new_rtt,to_kill))
    sys.exit(0)
        
