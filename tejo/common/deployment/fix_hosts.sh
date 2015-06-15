rm /tmp/hostname.txt

ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $1 hostname > /tmp/hostname.txt

n_lines=`cat /tmp/hostname.txt|wc -l`

if [ $n_lines -gt 0 ]; then
    host_name=`cat /tmp/hostname.txt`
    #sudo sh -c "echo \"$1 $host_name\" "
    sudo sh -c "echo \"$1 $host_name\" >> /etc/hosts"
fi 