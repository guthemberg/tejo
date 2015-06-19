add_ssh_key ()
{
	new_key_file=$1
	
	cd $HOME
	if [ ! -d .ssh ]
	then 
		mkdir .ssh
	fi
	cd .ssh
	if [ ! -e authorized_keys ]
	then 
		touch authorized_keys
	fi
	
	
	script_name=$1
	new_job_file=$2
	crontab -l | grep -v $script_name > /tmp/current_crontab
	cat $new_job_file >> /tmp/current_crontab
	crontab /tmp/current_crontab 
}

add_ssh_key $1