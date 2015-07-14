. /etc/tejo.conf

#echo -n "cleaning up... "

#sh /home/user/svc/experiments_scripts/ycsb/stop.sh;
#echo "done."

sed "s|RECORDCOUNT|$mongo_recordcount|g" /home/user/tejo/contrib/debian/mongodb/ycsb-0.1.4/workloads/load > /tmp/myload

sudo chmod ugo+x /home/user/tejo/contrib/debian/mongodb/ycsb-0.1.4/bin/ycsb

host_name=`hostname`

echo -n "loading new mongodb... "

#mongodb.maxconnections=1000 -threads 80
#mongodb.maxconnections=2000 -threads 200 
#mongodb.maxconnections=3000 -threads 300
/home/user/tejo/contrib/debian/mongodb/ycsb-0.1.4/bin/ycsb load mongodb -p mongodb.url="mongodb://${host_name}:27017" -p mongodb.database="ycsb" -p mongodb.writeConcern="normal" -p mongodb.maxconnections=2000 -threads 200 -s -P /tmp/myload

echo "done."