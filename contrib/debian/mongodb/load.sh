#echo -n "cleaning up... "

#sh /home/user/svc/experiments_scripts/ycsb/stop.sh;
#echo "done."

sudo chmod ugo+x /home/user/tejo/contrib/debian/mongodb/ycsb-0.1.4/bin/ycsb

host_name=`hostname`

echo -n "loading new mongodb... "

/home/user/tejo/contrib/debian/mongodb/ycsb-0.1.4/bin/ycsb load mongodb -p mongodb.url="mongodb://${host_name}:27017" -p mongodb.database="ycsb" -p mongodb.writeConcern="normal" -p mongodb.maxconnections=1000 -threads 40 -s -P /home/user/tejo/contrib/debian/mongodb/ycsb-0.1.4/workloads/load

echo "done."