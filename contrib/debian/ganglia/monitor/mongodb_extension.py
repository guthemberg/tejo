#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import copy
import subprocess
from subprocess import PIPE, Popen

from pymongo import MongoClient

NAME_PREFIX = 'mongodb_'
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
                ps_process=Popen(["pgrep","-f",process], stdout=PIPE)
                running=int(Popen(["wc","-l"], stdin=ps_process.stdout, stdout=PIPE,close_fds=True).communicate()[0].rstrip())
                if running>0:
                        return 1
                else:
                        return 0
        except:
                return 0

    
def get_metrics():
    """Return all metrics"""

    global METRICS, LAST_METRICS

    is_primary=0
    try:
        c = MongoClient()
        if c.is_primary:
            is_primary=1
    except:
        pass

    if (time.time() - METRICS['time']) > METRICS_CACHE_TTL:

        metrics = {}
        metrics['is_primary']=is_primary
        
        #active
        try:
            metrics['is_active']=running_process("mongod")
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





def metric_init(lparams):
    """Initialize metric descriptors"""

    global PARAMS

    # set parameters
    for key in lparams:
        PARAMS[key] = lparams[key]

    # define descriptors
    time_max = 60
    groups = 'mongodb'
    descriptors = [

        {
            'name': NAME_PREFIX + 'is_primary',
            'call_back': get_value,
            'time_max': time_max,
            'value_type': 'uint',
            'units': 'Yes: 1/ No: 0',
            'slope': 'both',
            'format': '%d',
            'description': 'Is This Primary',
            'groups': groups
        },
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

