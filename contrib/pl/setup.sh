#!/bin/sh

. /etc/tejo.conf


get_host_location()
{
        hostname|tr '-' '\n'|head -n1
}


##main

peer=$1
force_flag=no
if [ $# -eq 2 ]
then
	force_flag=$2
fi
	
me=`hostname`
location=`get_host_location`

ssh -i ${root_dir}/.ssh/id_rsa_cloud -o StrictHostKeyChecking=no -t $workload_user@$peer "wget --no-check-certificate https://raw.githubusercontent.com/guthemberg/yanoama/master/contrib/tejo/setup.sh -O /tmp/setup.sh"
if [ "$force_flag" = "yes" ]
then
	ssh -i ${root_dir}/.ssh/id_rsa_cloud -o StrictHostKeyChecking=no -t $workload_user@$peer "sh /tmp/setup.sh -l $location -d $default_domain -t workload -a $me -f yes"
else
	ssh -i ${root_dir}/.ssh/id_rsa_cloud -o StrictHostKeyChecking=no -t $workload_user@$peer "sh /tmp/setup.sh -l $location -d $default_domain -t workload -a $me"
fi
echo "stopping workload:"
#ssh -i ${root_dir}/.ssh/id_rsa_cloud -o StrictHostKeyChecking=no -t $workload_user@$peer "sh /home/${workload_user}/tejo/tejo/common/experiments_scripts/ycsb/stop.sh"
echo "stopped."
echo "running workload:"
ssh -i ${root_dir}/.ssh/id_rsa_cloud -o StrictHostKeyChecking=no -t -t $workload_user@$peer "touch /home/${workload_user}/wl_active.hit"
ssh -i ${root_dir}/.ssh/id_rsa_cloud -o StrictHostKeyChecking=no -t -t $workload_user@$peer "sh /home/${workload_user}/tejo/tejo/common/experiments_scripts/ycsb/run.sh 0 300 &"
echo "done"