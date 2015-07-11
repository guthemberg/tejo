echo -n "cleaning up... "

sh /home/user/svc/experiments_scripts/ycsb/stop.sh;
echo "done."

echo -n "loading new db... "

/home/user/svc/ycsb-0.1.4/bin/ycsb load mongodb -p mongodb.url="mongodb://datastore-001.svc.laas.fr:27017" -p mongodb.database="ycsb" -p mongodb.writeConcern="normal" -p mongodb.maxconnections=1000 -threads 40 -s -P /home/user/svc/ycsb-0.1.4/workloads/load

echo "done."