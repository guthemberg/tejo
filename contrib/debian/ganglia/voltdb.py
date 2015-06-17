#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import copy
import subprocess
from configobj import ConfigObj
import sys

#db api available in home_dir
conf_file = "/etc/tejo.conf"
config=ConfigObj(conf_file)
sys.path.append(config['home_dir'])
ALIVE_TIME=int(config['alive_time'])
#from database import MyDB

#available in home_dir
from tejo.common.db.voltdb.stats import VoltStats


NAME_PREFIX = 'voltdb_'
PARAMS = {
#fake example, TO DO: modify this
    'net_status' : '/usr/bin/netstat -s -p tcp'
}
METRICS = {
    'time' : 0,
    'data' : {}
}
LAST_METRICS = copy.deepcopy(METRICS)
METRICS_CACHE_TTL = 3

def running_process(process):
    try:
        ps_process=subprocess.Popen(["pgrep","-f",process], stdout=subprocess.PIPE)
        running=int(subprocess.Popen(["wc","-l"], stdin=ps_process.stdout, stdout=subprocess.PIPE,close_fds=True).communicate()[0].rstrip())
        if running>0:
            return 1
        else:
            return 0
    except:
            return 0
    
def get_metrics():
    """Return all metrics"""

    global METRICS, LAST_METRICS

    if (time.time() - METRICS['time']) > METRICS_CACHE_TTL:

        metrics = {}
    
        #voltdb metrics
        try:
            voltdb_stats=VoltStats()
            #all available stats are commented in https://voltdb.com/docs/UsingVoltDB/sysprocstatistics.php
            #The current resident set size. That is, the total amount of memory allocated to the VoltDB processes on the server.
            #Memory
            memory_counters=voltdb_stats.get_memory_counters()
            metrics['memory_rss']=float(memory_counters[0])
            metrics['memory_javaused']=float(memory_counters[1])
            metrics['memory_javaunused']=float(memory_counters[2])
            metrics['memory_tupledata']=float(memory_counters[3])
            metrics['memory_tupleallocated']=float(memory_counters[4])
            metrics['memory_indexmemory']=float(memory_counters[5])
            metrics['memory_stringmemory']=float(memory_counters[6])
            metrics['memory_tuplecount']=float(memory_counters[7])
            metrics['memory_pooledmemory']=float(memory_counters[8])
            #DR
            dr_counters=voltdb_stats.get_dr_counters()
            metrics['dr_total_bytes']=float(dr_counters[0])
            metrics['dr_total_bytes_in_memory']=float(dr_counters[1])
            metrics['dr_total_buffers']=float(dr_counters[2])
            
            #partition count
            metrics['partition_count']=float(voltdb_stats.get_partition_count())
            
            #planner
            planner_counters=voltdb_stats.get_planner_counters()
            metrics['planner_partitions']=float(planner_counters[0])
            metrics['planner_cache1_hits']=float(planner_counters[1])
            metrics['planner_cache2_hits']=float(planner_counters[2])
            metrics['planner_cache_misses']=float(planner_counters[3])
            metrics['planner_failures']=float(planner_counters[4])
            
            #procedure
            #(invocations,timed_invocations, avg_execution_time,aborts,failures)
            (metrics['procedure_invocations'],metrics['procedure_timed_invocations'], \
             metrics['procedure_avg_execution_time'],metrics['procedure_aborts'], \
             metrics['procedure_failures'])=voltdb_stats.get_procedure_counters()

            voltdb_stats.close()
        except:        
            metrics['memory_rss']=0.0
            metrics['memory_javaused']=0.0
            metrics['memory_javaunused']=0.0
            metrics['memory_tupledata']=0.0
            metrics['memory_tupleallocated']=0.0
            metrics['memory_indexmemory']=0.0
            metrics['memory_stringmemory']=0.0
            metrics['memory_tuplecount']=0.0
            metrics['memory_pooledmemory']=0.0
            metrics['dr_total_bytes']=0.0
            metrics['dr_total_bytes_in_memory']=0.0
            metrics['dr_total_buffers']=0.0
            metrics['partition_count']=0.0
            metrics['planner_partitions']=0.0
            metrics['planner_cache1_hits']=0.0
            metrics['planner_cache2_hits']=0.0
            metrics['planner_cache_misses']=0.0
            metrics['planner_failures']=0.0
            metrics['procedure_invocations']=0.0
            metrics['procedure_timed_invocations']=0.0
            metrics['procedure_avg_execution_time']=0.0
            metrics['procedure_aborts']=0.0
            metrics['procedure_failures']=0.0
        #active
        try:
            metrics['is_active']=running_process("voltdb")
        except:
            metrics['is_active']=0

        # update cache
        LAST_METRICS = copy.deepcopy(METRICS)
        METRICS = {
            'time': time.time(),
            'data': metrics
        }

    return [METRICS, LAST_METRICS]



def get_value(name):
    """Return a value for the requested metric"""

    # get metrics
    metrics = get_metrics()[0]

    # get value
    name = name[len(NAME_PREFIX):] # remove prefix from name
    try:
        result = metrics['data'][name]
    except StandardError:
        result = 0

    return result

def get_rate(name):
    """Return change over time for the requested metric"""

    # get metrics
    [curr_metrics, last_metrics] = get_metrics()

    # get rate
    name = name[len(NAME_PREFIX):] # remove prefix from name

    try:
        rate = float(curr_metrics['data'][name] - last_metrics['data'][name]) / \
               float(curr_metrics['time'] - last_metrics['time'])
        if rate < 0:
            rate = float(0)
    except StandardError:
        rate = float(0)

    return rate



def metric_init(lparams):
    """Initialize metric descriptors"""

    global PARAMS

    # set parameters
    for key in lparams:
        PARAMS[key] = lparams[key]

    # define descriptors
    time_max = 60
    groups = 'voltdb'
    descriptors = [
        {
            'name': NAME_PREFIX + 'is_active',
            'call_back': get_value,
            'time_max': time_max,
            'value_type': 'uint',
            'units': 'Yes: 1/ No: 0',
            'slope': 'both',
            'format': '%d',
            'description': 'Is Active',
            'groups': groups
        },
        {
           'name': NAME_PREFIX + 'memory_rss',
           'call_back': get_value,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'kilobytes',
           'slope': 'both',
           'format': '%f',
           'description': 'Memory Resident Set Size',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'memory_javaused',
           'call_back': get_value,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'kilobytes',
           'slope': 'both',
           'format': '%f',
           'description': 'Memory for Java and in use',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'memory_javaunused',
           'call_back': get_value,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'kilobytes',
           'slope': 'both',
           'format': '%f',
           'description': 'Memory for Java but unused',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'memory_tupledata',
           'call_back': get_value,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'kilobytes',
           'slope': 'both',
           'format': '%f',
           'description': 'Memory for storing db records',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'memory_tupleallocated',
           'call_back': get_value,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'kilobytes',
           'slope': 'both',
           'format': '%f',
           'description': 'Memory for db records and free space',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'memory_indexmemory',
           'call_back': get_value,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'kilobytes',
           'slope': 'both',
           'format': '%f',
           'description': 'Memory for db indexes',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'memory_stringmemory',
           'call_back': get_value,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'kilobytes',
           'slope': 'both',
           'format': '%f',
           'description': 'Memory for in-line records',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'memory_tuplecount',
           'call_back': get_value,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'records',
           'slope': 'both',
           'format': '%f',
           'description': 'Total number of database records now',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'memory_pooledmemory',
           'call_back': get_value,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'megabytes',
           'slope': 'both',
           'format': '%f',
           'description': 'Memory for other tasks',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'dr_total_bytes',
           'call_back': get_value,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'bytes',
           'slope': 'both',
           'format': '%f',
           'description': 'Current queue length to DR',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'dr_total_bytes_in_memory',
           'call_back': get_value,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'bytes',
           'slope': 'both',
           'format': '%f',
           'description': 'Queued data currently held in memory',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'dr_total_buffers',
           'call_back': get_value,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'number of',
           'slope': 'both',
           'format': '%f',
           'description': 'Waiting buffers in this partition',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'partition_count',
           'call_back': get_value,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'number of',
           'slope': 'both',
           'format': '%f',
           'description': 'Unique or logical partitions on the cluster',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'planner_partitions',
           'call_back': get_value,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'partitions',
           'slope': 'both',
           'format': '%f',
           'description': 'Number of partitions',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'planner_cache1_hits',
           'call_back': get_rate,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'queries',
           'slope': 'both',
           'format': '%f',
           'description': 'Queries that matched and reused in cache1',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'planner_cache2_hits',
           'call_back': get_rate,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'queries',
           'slope': 'both',
           'format': '%f',
           'description': 'Queries that matched and reused in cache2',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'planner_cache_misses',
           'call_back': get_rate,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'queries',
           'slope': 'both',
           'format': '%f',
           'description': 'Queries that had no match in the cache',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'planner_failures',
           'call_back': get_rate,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'events',
           'slope': 'both',
           'format': '%f',
           'description': 'Planning for an ad hoc query failed',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'procedure_aborts',
           'call_back': get_rate,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'aborts',
           'slope': 'both',
           'format': '%f',
           'description': 'Aborted procedures',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'procedure_failures',
           'call_back': get_rate,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'failures',
           'slope': 'both',
           'format': '%f',
           'description': 'Procedure failed unexpectedly',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'procedure_invocations',
           'call_back': get_rate,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'invocations',
           'slope': 'both',
           'format': '%f',
           'description': 'Procedures invocations',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'procedure_timed_invocations',
           'call_back': get_value,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'invocations',
           'slope': 'both',
           'format': '%f',
           'description': 'Number of invocations for avg,min,max',
           'groups': groups
        },
        {
           'name': NAME_PREFIX + 'procedure_avg_execution_time',
           'call_back': get_value,
           'time_max': time_max,
           'value_type': 'float',
           'units': 'nanoseconds',
           'slope': 'both',
           'format': '%f',
           'description': 'Avg time to execute the stored procedure',
           'groups': groups
        }
 
    ]

    return descriptors


def metric_cleanup():
    """Cleanup"""

    pass


# the following code is for debugging and testing
if __name__ == '__main__':
    descriptors = metric_init(PARAMS)
    while True:
        for d in descriptors:
            print (('%s = %s') % (d['name'], d['format'])) % (d['call_back'](d['name']))
        print ''
        time.sleep(METRICS_CACHE_TTL)

