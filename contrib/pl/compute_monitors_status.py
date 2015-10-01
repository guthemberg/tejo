import pickle,sys,subprocess
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
        peering_table_file=tejo_config['root_dir']+"/peering.pck"
        peering_table=load_object_from_file(peering_table_file)
        list_of_monitors_file=sys.argv[1]
        monitors_status_table=load_object_from_file(list_of_monitors_file)
        monitors={}
        best=''
        balance=''
        score=-1
        crowd=-1
        for node in monitors_status_table:
            monitor=node['monitor']
            if 'score' in node.keys() and  'crowd' in node.keys() and (monitor in peering_table):
                if len(best)==0:
                    best=monitor
                    score=node['score']
                    crowd=node['crowd']
                else:
                    if ((node['crowd']*3) - node['score']) > ((crowd*3)-score):
                        best=monitor
                        score=node['score']
                        crowd=node['crowd']
                        
                if len(balance)==0:
                    balance=monitor
                    score=node['score']
                    crowd=node['crowd']
                else:
                    if node['crowd'] < crowd:
                        balance=monitor
                        score=node['score']
                        crowd=node['crowd']
                

        strategy=sys.argv[2]
        if strategy == 'best' and len(best)>0:
            sys.stdout.write(best)
            sys.exit(0)
        elif strategy == 'balance' and len(balance)>0:
            sys.stdout.write(balance)
            sys.exit(0)
        else:
            sys.stdout.write('')
            sys.exit(1)
            
    except:
        sys.stdout.write('')
        sys.exit(1)

            
        
