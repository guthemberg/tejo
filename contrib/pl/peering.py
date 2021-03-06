import pickle,sys,socket,subprocess,os,random
from datetime import datetime
from time import mktime,sleep
#from planetlab import Monitor
from configobj import ConfigObj


PLE_CONF_FILE='/etc/ple.conf'
TEJO_CONF_FILE='/etc/tejo.conf'



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

def load_object_from_file(input_file):
    return pickle.load( open( input_file, "rb" ) )

def save_object_to_file(myobject,output_file):
    f = open(output_file,'w')
    pickle.dump(myobject, f)
    f.close()
    
    
if __name__ == '__main__':
    try:
        tejo_config=ConfigObj(TEJO_CONF_FILE)
        path_to_yanoama='/home/'+tejo_config['workload_user']+'/yanoama'
        list_of_monitors=sys.argv[1]
        peering_table_file=tejo_config['root_dir']+"/peering.pck"
        peering_table={}
        if os.path.isfile(peering_table_file):
            peering_table=load_object_from_file(peering_table_file)
        smallest_rtt=0.0
        target=tejo_config['workload_target']
        for monitor in load_object_from_file(list_of_monitors):
            if int(tejo_config['system_id'])==0:
                rtt=getRTT_TCP(monitor, path_to_yanoama,27017)
            else:
                rtt=getRTT_TCP(monitor, path_to_yanoama)
            if monitor in peering_table:
                if rtt<peering_table[monitor] and rtt>0 and rtt<int(tejo_config['max_neighbourhood_rtt']):
                    peering_table[monitor]=rtt
                if rtt == -1:
                    del peering_table[monitor]
            else:
                if rtt>0 and rtt<int(tejo_config['max_neighbourhood_rtt']):
                    peering_table[monitor]=rtt
            if monitor in peering_table:
                if smallest_rtt==0.0 or peering_table[monitor]<smallest_rtt:
                    smallest_rtt=peering_table[monitor]
                    target=monitor
                    
        save_object_to_file(peering_table, peering_table_file)
        sys.stdout.write(target)
        sys.exit(0)
    except:
        sys.stdout.write('')
        sys.exit(1)

            
        
