#!/bin/sh


. /etc/tejo.conf


num=`pgrep -f setup_peers.py|wc -l`
echo $num

index=1

while [ "$num" -gt 0 ]
do
	echo "running $num setup_peer.py, sleeping 150s"
	sleep 150
	if [ "$index" -eq 2 ]; then
		pkill -f setup_peers.py
        break
	fi
	num=`pgrep -f setup_peers.py|wc -l`
	index=`expr $index + 1`
done





if [ ! -z $workload_setup_peers ]; then
	if [ $workload_setup_peers != 'yes' ]; then
		echo "workload_setup_peers in /etc/tejo.conf (${workload_setup_peers}) should be 'yes' to launch peers setup. Bye." 
		exit
	fi
else
	echo "workload_setup_peers should exist in /etc/tejo.conf and be 'yes' to launch peers setup. Bye." 
	exit
fi


#this verifies if the host is available to setup and if it is recheable through 22 port 
peer_to_setup=`python $home_dir/tejo/common/experiments_scripts/peers/setup_peers.py`

if [ $? -eq 0 ]
then
#this checks if whe can connect to the node using workload user

    target=${workload_user}@${peer_to_setup}
    key=${root_dir}/.ssh/id_rsa_cloud
    echo $target
    ssh -i $key -o StrictHostKeyChecking=no -o PasswordAuthentication=no -o ConnectTimeout=5 -o ServerAliveInterval=5 $target "pwd"

	if [ $? -eq 0 ]
	then
		ts=`date`
		echo "[$ts]$peer_to_setup" >> /tmp/peers_to_setup_history.log
		/bin/sh $home_dir/contrib/pl/setup.sh $peer_to_setup $workload_force_setup
#	target="workload_user@peer_to_setup"
#	checking_result=`ssh -i ${root_dir}/.ssh/id_rsa_cloud -o StrictHostKeyChecking=no -o PasswordAuthentication=no -o ConnectTimeout=60 -o ServerAliveInterval=60 $target sh /home/${workload_user}/tejo/tejo/common/experiments_scripts/peers/check_running_peer.sh`
#	if [ $? -eq 0 ]
#	then
#		python $home_dir/tejo/common/experiments_scripts/peers/setup_peers.py $peer_to_setup
			exit 0
#	else
#		exit 1
#	fi
	else
		python $home_dir/tejo/common/experiments_scripts/peers/setup_peers.py $peer_to_setup True
	fi


fi
exit 1

if [ $? -eq 0 ]
then
	ts=`date`
	echo "[$ts]$peer_to_setup" >> /tmp/peers_to_setup_history.log
	/bin/sh $home_dir/contrib/pl/setup.sh $peer_to_setup $workload_force_setup
#	target="workload_user@peer_to_setup"
#	checking_result=`ssh -i ${root_dir}/.ssh/id_rsa_cloud -o StrictHostKeyChecking=no -o PasswordAuthentication=no -o ConnectTimeout=60 -o ServerAliveInterval=60 $target sh /home/${workload_user}/tejo/tejo/common/experiments_scripts/peers/check_running_peer.sh`
#	if [ $? -eq 0 ]
#	then
#		python $home_dir/tejo/common/experiments_scripts/peers/setup_peers.py $peer_to_setup
		exit 0
#	else
#		exit 1
#	fi
fi
exit 1
		
	
#	
#	',target,'pwd'],stdout=subprocess.PIPE,close_fds=True)
#
'/home/'+tejo_config['workload_user']+'/tejo/tejo/common/experiments_scripts/peers/check_running_peer.sh
#        cmd.communicate()[0].strip()
#        if cmd.returncode == 0:
#            return True
#        return False
#
#
#fi
#
#    peer_to_setup=candidates[random.randrange(0,len(candidates))]
#        
#    script_path=tejo_config['home_dir']+'/contrib/pl/setup.sh'
#    script_output = subprocess.Popen(['/bin/sh',script_path,peer_to_setup], stdout=subprocess.PIPE, close_fds=True).communicate()[0]
#    script_path='/home/'+tejo_config['workload_user']+'/tejo/tejo/common/experiments_scripts/peers/check_running_peer.sh'
#    key=tejo_config['root_dir']+"/.ssh/id_rsa_cloud"
#    ssh_args=tejo_config['workload_user']+"@"+peer_to_setup    
#    script_output = subprocess.Popen(['ssh','-i', key, "-o", "StrictHostKeyChecking=no", "-t", ssh_args,'/bin/sh',script_path], stdout=subprocess.PIPE, close_fds=True).communicate()[0].strip()
#    print "script output: (%s)"%script_output
#    if script_output=='ok':
#print '%s: ok!' % peer_to_setup
#setup_peers_status[peer_to_setup]['active']=True
#        save_object_to_file(setup_peers_status, setup_peers_status_file)
#    else:
#        print '%s: failed!' % peer_to_setup
#
#
#
#    print "[%s]:done."%(str(datetime.now()))  
