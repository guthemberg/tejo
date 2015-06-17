import sys
import subprocess
from configobj import ConfigObj

#db api available in home_dir
conf_file = "/etc/tejo.conf"
config=ConfigObj(conf_file)
sys.path.append(config['home_dir'])
#from database import MyDB

#available in home_dir
from tejo.common.db.voltdb.voltdbclient import *

class VoltStats:
    
    def __init__(self,\
                 server=(subprocess.Popen(["hostname"], stdout=subprocess.PIPE, \
                                          close_fds=True).communicate()[0].rstrip())):
        self._hostname=server
        self._client = FastSerializer(server, 21212)
        self._stats = VoltProcedure(self._client, "@Statistics", \
                               [ FastSerializer.VOLTTYPE_STRING, \
                                FastSerializer.VOLTTYPE_INTEGER ] )
        self._host_id=0
        response = self._stats.call([ "memory", 0 ])
        for t in response.tables:
            for row in t.tuples:
                if row[2] == self._hostname:
                    self._host_id=int(row[1])
                    

    ##Memory
    def get_memory_counters(self):
        start_index=3
        end_index=11
        counters = [0,0,0,0,0,0,0,0,0]
        response = self._stats.call([ "memory", 0 ])
        for t in response.tables:
            for row in t.tuples:
                if row[1] == self._host_id:
                    for i in range(start_index,(end_index+1)):
                        counters[i-start_index]=int(row[i])
        return counters
         
    def get_memory_rss(self):
        # Check memory
        response = self._stats.call([ "memory", 0 ])
        for t in response.tables:
            for row in t.tuples:
                if row[1] == self._host_id:
                    return int(row[3])
        return 0

    def get_memory_javaused(self):
        # Check memory
        response = self._stats.call([ "memory", 0 ])
        for t in response.tables:
            for row in t.tuples:
                if row[1] == self._host_id:
                    return int(row[4])
        return 0

    def get_memory_javaunused(self):
        # Check memory
        response = self._stats.call([ "memory", 0 ])
        for t in response.tables:
            for row in t.tuples:
                if row[1] == self._host_id:
                    return int(row[5])
        return 0

    def get_memory_tupledata(self):
        # Check memory
        response = self._stats.call([ "memory", 0 ])
        for t in response.tables:
            for row in t.tuples:
                if row[1] == self._host_id:
                    return int(row[6])
        return 0

    def get_memory_tupleallocated(self):
        # Check memory
        response = self._stats.call([ "memory", 0 ])
        for t in response.tables:
            for row in t.tuples:
                if row[1] == self._host_id:
                    return int(row[7])
        return 0

    def get_memory_indexmemory(self):
        # Check memory
        response = self._stats.call([ "memory", 0 ])
        for t in response.tables:
            for row in t.tuples:
                if row[1] == self._host_id:
                    return int(row[8])
        return 0

    def get_memory_stringmemory(self):
        # Check memory
        response = self._stats.call([ "memory", 0 ])
        for t in response.tables:
            for row in t.tuples:
                if row[1] == self._host_id:
                    return int(row[9])
        return 0

    def get_memory_tuplecount(self):
        # Check memory
        response = self._stats.call([ "memory", 0 ])
        for t in response.tables:
            for row in t.tuples:
                if row[1] == self._host_id:
                    return int(row[10])
        return 0

    def get_memory_pooledmemory(self):
        # Check memory
        response = self._stats.call([ "memory", 0 ])
        for t in response.tables:
            for row in t.tuples:
                if row[1] == self._host_id:
                    return int(row[11])
        return 0
    
    ##DR, that stands for database replication status
    def get_dr_counters(self):
        counters=[0,0,0]
        # Check memory
        response = self._stats.call([ "dr", 0 ])
        table_counter=1
        for t in response.tables:
            if table_counter==1:
                for row in t.tuples:
                    if row[1] == self._host_id:
                        counters[0]=counters[0]+row[5]
                        counters[1]=counters[1]+row[6]
                        counters[2]=counters[2]+row[7]
                table_counter=table_counter+1
                
        return counters
    
    #PARTITIONCOUNT
    def get_partition_count(self):
        # Check memory
        response = self._stats.call([ "partitioncount", 0 ])
        for t in response.tables:
            for row in t.tuples:
                if row[1] == self._host_id:
                    return int(row[3])
        return 0

    #PLANNER
    def get_planner_counters(self):
        # Check memory
        counters=[0,0,0,0,0]
        response = self._stats.call([ "planner", 0 ])
        for t in response.tables:
            for row in t.tuples:
                if row[1] == self._host_id:
                    if int(row[4]) != (-1):
                        counters[0]=counters[0]+1
                        counters[1]=counters[1]+int(row[7])
                        counters[2]=counters[2]+int(row[8])
                        counters[3]=counters[3]+int(row[9])
                        counters[4]=counters[4]+int(row[13])

        return counters

    #procedure
    def get_procedure_counters(self):
        # Check memory
        invocations=0
        timed_invocations=0
        avg_execution_time=0
        aborts=0
        failures=0
        response = self._stats.call([ "procedure", 0 ])
        for t in response.tables:
            for row in t.tuples:
                if row[1] == self._host_id:
                    invocations=invocations+int(row[6])
                    timed_invocations=timed_invocations+int(row[7])
                    avg_execution_time=avg_execution_time+int(row[10])
                    aborts=aborts+int(row[17])
                    failures=failures+int(row[18])

        return (float(invocations),float(timed_invocations), float(avg_execution_time),float(aborts),float(failures))


    def close(self):
        if self._client is not None:
            self._client.close()

    def __del__(self):
        if self._client is not None:
            self._client.close()

