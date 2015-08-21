#!/bin/sh



#how to call is
# sh run.sh
# or
# sh run.sh SYSTEM_ID OPERATIONS_PER_SECOND
#where 	SYSTEM_ID might be 0 or 2
#		OPERATION PER SECOND 50
. /etc/tejo.conf



install_ganglia_monitor()
{

	
	location=$1
	node_type=$2
	aggregator=$3
	
	
	#install ganglia and get tejo
	#this allows to install required packages 
	sudo yum --nogpgcheck -y -d0 -e0 --quiet install ganglia-gmond ganglia-gmond-python ganglia-devel
	get_tejo
	
	home_dir="`get_home_dir`"
	gmond_conf_dir=""
	dst_conf_file="/etc/ganglia/gmond.conf"
	if [ `rpm -qa|grep ganglia-gmond-python|wc -l` -eq 1 ]
	then
		sudo /sbin/service gmond restart
		if [ ! -e /etc/ganglia/gmond.conf.original ]
		then
			sudo cp /etc/ganglia/gmond.conf /etc/ganglia/gmond.conf.original
		fi
		gmond_conf_dir=`/usr/sbin/gmond -t|grep conf.d|cut -f2 -d\'|cut -f1-4 -d/`
		cp ${home_dir}/contrib/fedora/ganglia/gmond.conf.sample /tmp/gmond.conf.1

	else
		sudo /sbin/service gmond stop
		sudo yum --nogpgcheck -y -d0 -e0 --quiet remove ganglia-gmond ganglia-gmond-python ganglia-devel
		install_confuse
		install_gmond_from_sources
		if [ ! -e /usr/local/etc/gmond.conf ]
		then
			sudo su -c "/usr/local/sbin/gmond -t > /usr/local/etc/gmond.conf"
		fi
		if [ ! -e /usr/local/etc/gmond.conf.original ]
		then
			sudo cp /usr/local/etc/gmond.conf /usr/local/etc/gmond.conf.original
		fi
		sudo cp ${home_dir}/contrib/fedora/ganglia/init.d/gmond /etc/init.d/
		sudo chmod guo+x /etc/init.d/gmond
		#sudo update-rc.d gmond defaults
		sudo /sbin/service gmond restart
		gmond_conf_dir=`/usr/local/sbin/gmond -t|grep conf.d|cut -f2 -d\"|cut -f1-5 -d/`
		dst_conf_file="/usr/local/etc/gmond.conf"
		python_modules_dir=`grep python_modules ${gmond_conf_dir}/modpython.conf|cut -f2 -d=|sed "s|\"||g"`
		if [ ! -e $python_modules_dir ]
		then
			sudo mkdir -p $python_modules_dir
		fi
		sed "s|etc\/ganglia|usr\/local\/etc|g" ${home_dir}/contrib/fedora/ganglia/gmond.conf.sample > /tmp/gmond.conf.1
	fi

#	echo 'deb http://ftp.univ-pau.fr/linux/mirrors/debian/ wheezy main'| sudo tee /etc/apt/sources.list.d/ganglia.list
#	sudo gpg --keyserver pgpkeys.mit.edu --recv-key  8B48AD6246925553
#	sudo gpg --keyserver pgpkeys.mit.edu --recv-key  6FB2A1C265FFB764
#	sudo gpg -a --export 6FB2A1C265FFB764 | sudo apt-key add -
#	sudo gpg -a --export 8B48AD6246925553 | sudo apt-key add -
#	sudo apt-get -q -y update
#	sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y install ganglia-modules-linux ganglia-monitor ganglia-monitor-python
#	if [ -e /etc/ganglia/conf.d/diskusage.pyconf ]
#	then
#		sudo mv /etc/ganglia/conf.d/diskusage.pyconf /etc/ganglia/conf.d/diskusage.pyconf.disabled
#	fi	
	#	sudo service ganglia-monitor restart
	#	sudo rm /etc/apt/sources.list.d/ganglia.list
	#	sudo apt-get -q -y update
		
#	if [ -e /etc/ganglia/conf.d/tcpconn.pyconf.disabled ]
#	then
#		sudo mv /etc/ganglia/conf.d/tcpconn.pyconf.disabled /etc/ganglia/conf.d/tcpconn.pyconf
#	fi
		


		
	case "$node_type" in
		"vm")
			source="VMs"
			gmond_port=${default_gmond_port}
			sed "s|LOCATION|$location|g" ${home_dir}/contrib/fedora/ganglia/gmond.conf.sample | sed "s|SOURCE|$source|g" | sed "s|PORT|$gmond_port|g" | sed "s|TARGET|$aggregator|g" > /tmp/gmond.conf
						
			sudo cp ${home_dir}/contrib/fedora/ganglia/vm/*.pyconf ${gmond_conf_dir}/
			sudo cp ${home_dir}/contrib/fedora/ganglia/vm/*.py `grep python_modules ${gmond_conf_dir}/modpython.conf|cut -f2 -d=|sed "s|\"||g"`/
	
						
			;;
			
		*)
			source="workload"
			gmond_port=${wl_gmond_port}
			sed "s|LOCATION|$location|g" /tmp/gmond.conf.1 | sed "s|SOURCE|$source|g" | sed "s|PORT|$gmond_port|g" | sed "s|TARGET|$aggregator|g" > /tmp/gmond.conf
			sudo cp ${home_dir}/contrib/fedora/ganglia/wl/*.pyconf ${gmond_conf_dir}/
			sudo cp ${home_dir}/contrib/fedora/ganglia/wl/*.py `grep python_modules ${gmond_conf_dir}/modpython.conf|cut -f2 -d=|sed "s|\"||g"`/
			;;
		
	esac

	sudo mv /tmp/gmond.conf $dst_conf_file
				
	#enabled by default	
	#sudo update-rc.d ganglia-monitor defaults
	
	sudo /sbin/chkconfig gmond on
	
	sudo /sbin/service gmond restart
}


### main

n_fields=`echo $monitors_list_file| tr '/' '\n' | wc -l`
monitors_file=`echo $monitors_list_file |cut -d/ -f$n_fields`

if [ ! -e ${root_dir}/$monitors_file ]
then
	wget --no-check-certificate http://$workload_target/$monitors_file -O ${root_dir}/$monitors_file
else
	python -c "import pickle ; print pickle.load( open( '${root_dir}/$monitors_file', 'rb' ) )"
	if [ ! $? -eq 0 ]
	then
		rm ${root_dir}/$monitors_file
		wget --no-check-certificate http://$workload_target/$monitors_file -O ${root_dir}/$monitors_file
		#doubling checking
		python -c "import pickle ; print pickle.load( open( '${root_dir}/$monitors_file', 'rb' ) )"
		if [ ! $? -eq 0 ]
		then
			echo "sorry failed to get the monitors list ${root_dir}/$monitors_file"
			exit 1
		fi
	fi 
fi

#this returns the nearest target
target=`python ${home_dir}/contrib/pl/peering.py ${root_dir}/$monitors_file`

if [ "$workload_target" != "$target" -a `expr length "$target"` -gt 0 ]
then
	if [ "$workload_strategy" = "nearest" ]
	then
		rm $workload_rtt
		node_location=`echo $target|tr '-' '\n'|head -n1`
		install_ganglia_monitor "$node_location" "$node_type" "$target"
		sudo sed -i "s|$workload_target|$target|g" /etc/tejo.conf

		/bin/sh /home/`whoami`/tejo/tejo/common/experiments_scripts/ycsb/stop.sh
		touch ${mongo_active_wl_file}
		/bin/sh /home/`whoami`/tejo/contrib/pl/check_workload.sh 
			
	fi
fi
