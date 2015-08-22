#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# MongoDB gmond module for Ganglia
#
# Copyright (C) 2011 by Michael T. Conigliaro <mike [at] conigliaro [dot] org>.
# All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import socket
import time
import copy

import pickle,os
#from planetlab import Monitor
from configobj import ConfigObj

TEJO_CONF_FILE='/etc/tejo.conf'

NAME_PREFIX = 'slo_'
PARAMS = {
    'net_status' : '/usr/bin/netstat -s -p tcp'
}
METRICS = {
    'time' : 0,
    'data' : {}
}
LAST_METRICS = copy.deepcopy(METRICS)
METRICS_CACHE_TTL = 3

def load_object_from_file(input_file):
    return pickle.load( open( input_file, "rb" ) )


def get_metrics():
    """Return all metrics"""

    global METRICS, LAST_METRICS

    if (time.time() - METRICS['time']) > METRICS_CACHE_TTL:

        metrics = {}
        
        tejo_config=ConfigObj(TEJO_CONF_FILE)

        #violations
        try:
            metrics['violation']=int(''.join(open('/tmp/slo_violation.txt', 'r').readlines()).strip())
        except :
            metrics['violation']=int(0)
        
        #throughput
        try:
            metrics['throughput']=float(''.join(open('/tmp/slo_throughput.txt', 'r').readlines()).strip())
        except :
            metrics['throughput']=float(0)

        #rtt
        try:
            metrics['rtt']=float(load_object_from_file(tejo_config['workload_rtt']))
        except :
            metrics['rtt']=float(0.0)
            
        #fresh service rtt
        try:
            metrics['service_rtt']=float(load_object_from_file(tejo_config['workload_service_rtt']))
        except :
            metrics['service_rtt']=float(0.0)
            
            
        ##workload death
        try:
            if (load_object_from_file(tejo_config['workload_death_file'])):
                metrics['death']=int(1)
            else:
                metrics['death']=int(0)
        except :
            metrics['death']=int(0)

        ##workload death
        try:
            metrics['outliers']=load_object_from_file(tejo_config['workload_outliers_file'])
        except :
            metrics['outliers']=int(0)


        #target throughput
        try:
            metrics['target_throughput']=int(''.join(open('/tmp/slo_target_throughput.txt', 'r').readlines()).strip())
        except :
            metrics['target_throughput']=int(0)
       
        #latency
        #99th ALL
        try:
            metrics['latency_99th']=int(''.join(open('/tmp/slo_latency_99th.txt', 'r').readlines()).strip())
        except :
            metrics['latency_99th']=int(0)
        #max 99th ALL
        try:
            metrics['max_latency_99th']=int(''.join(open('/tmp/slo_max_latency_99th.txt', 'r').readlines()).strip())
        except :
            metrics['max_latency_99th']=int(0)
        #95th ALL
        try:
            metrics['latency_95th']=int(''.join(open('/tmp/slo_latency_95th.txt', 'r').readlines()).strip())
        except :
            metrics['latency_95th']=int(0)
        #max 95th ALL
        try:
            metrics['max_latency_95th']=int(''.join(open('/tmp/slo_max_latency_95th.txt', 'r').readlines()).strip())
        except :
            metrics['max_latency_95th']=int(0)
        #latency avg
        try:
            metrics['latency_avg']=int(float(''.join(open('/tmp/slo_latency_avg.txt', 'r').readlines()).strip()))
        except :
            metrics['latency_avg']=int(0)
        #max latency avg
        try:
            metrics['max_latency_avg']=int(''.join(open('/tmp/slo_max_latency_avg.txt', 'r').readlines()).strip())
        except :
            metrics['max_latency_avg']=int(0)
        
        #service id
        try:
            metrics['system_id']=int(''.join(open('/tmp/slo_system_id.txt', 'r').readlines()).strip())
        except :
            metrics['system_id']=int(0)
                
#             metrics_str = ''.join(io.readlines()).strip() # convert to string
#             metrics_str = re.sub('\w+\((.*)\)', r"\1", metrics_str) # remove functions

            # convert to flattened dict
#             try:
#                 if status_type == 'net_status':
#                     metrics.update(flatten(json.loads(metrics_str)))
#                 else:
#                     metrics.update(flatten(json.loads(metrics_str), pre='%s_' % status_type))
#             except ValueError:
#                 metrics = {}

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



def get_globalLock_ratio(name):
    """Return the global lock ratio"""

    try:
        result = get_rate(NAME_PREFIX + 'globalLock_lockTime') / \
                 get_rate(NAME_PREFIX + 'globalLock_totalTime') * 100
    except ZeroDivisionError:
        result = 0

    return result


def get_indexCounters_btree_miss_ratio(name):
    """Return the btree miss ratio"""

    try:
        result = get_rate(NAME_PREFIX + 'indexCounters_btree_misses') / \
                 get_rate(NAME_PREFIX + 'indexCounters_btree_accesses') * 100
    except ZeroDivisionError:
        result = 0

    return result


def get_connections_current_ratio(name):
    """Return the percentage of connections used"""

    try:
        result = float(get_value(NAME_PREFIX + 'connections_current')) / \
                 float(get_value(NAME_PREFIX + 'connections_available')) * 100
    except ZeroDivisionError:
        result = 0

    return result


def get_slave_delay(name):
    """Return the replica set slave delay"""

    # get metrics
    metrics = get_metrics()[0]

    # no point checking my optime if i'm not replicating
    if 'rs_status_myState' not in metrics['data'] or metrics['data']['rs_status_myState'] != 2:
        result = 0

    # compare my optime with the master's
    else:
        master = {}
        slave = {}
        try:
            for member in metrics['data']['rs_status_members']:
                if member['state'] == 1:
                    master = member
                if member['name'].split(':')[0] == socket.getfqdn():
                    slave = member
            result = max(0, master['optime']['t'] - slave['optime']['t']) / 1000
        except KeyError:
            result = 0

    return result


def get_asserts_total_rate(name):
    """Return the total number of asserts per second"""

    return float(reduce(lambda memo,obj: memo + get_rate('%sasserts_%s' % (NAME_PREFIX, obj)),
                       ['regular', 'warning', 'msg', 'user', 'rollovers'], 0))


def metric_init(lparams):
    """Initialize metric descriptors"""

    global PARAMS

    # set parameters
    for key in lparams:
        PARAMS[key] = lparams[key]

    # define descriptors
    time_max = 60
    groups = 'slo'
    descriptors = [
#         {
#             'name': NAME_PREFIX + 'tcp_retransmitted_bytes',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'bytes/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP retransmitted bytes',
#             'groups': groups
#         },
#         {
#             'name': NAME_PREFIX + 'tcp_retransmitted_packets',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'packets/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP retransmitted packets',
#             'groups': groups
#         },#
#         {
#             'name': NAME_PREFIX + 'tcp_control_packets',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'packets/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP control packets',
#             'groups': groups
#         },
#          {
#              'name': NAME_PREFIX + 'tcp_ack_only_packets',
#              'call_back': get_rate,
#              'time_max': time_max,
#              'value_type': 'float',
#              'units': 'packets/sec',
#              'slope': 'both',
#              'format': '%f',
#              'description': 'TCP ack-only packets',
#              'groups': groups
#          },
#          {
#             'name': NAME_PREFIX + 'tcp_acks_bytes',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'bytes/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP acks bytes',
#             'groups': groups
#          },
#          {
#             'name': NAME_PREFIX + 'tcp_acks_packets',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'packets/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP ACKs packets',
#             'groups': groups
#          },#
#          {
#             'name': NAME_PREFIX + 'tcp_duplicate_acks',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'acks/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP duplicate acks',
#             'groups': groups
#          },
#          {
#             'name': NAME_PREFIX + 'tcp_received_in_sequence_bytes',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'bytes/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP received in-sequence bytes',
#             'groups': groups
#          },
#          {
#             'name': NAME_PREFIX + 'tcp_received_in_sequence_packets',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'packets/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP received in-sequence packets',
#             'groups': groups
#          },#
#          {
#             'name': NAME_PREFIX + 'tcp_completely_duplicate_bytes',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'bytes/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP completely duplicate bytes',
#             'groups': groups
#          },#
#          {
#             'name': NAME_PREFIX + 'tcp_completely_duplicate_packets',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'packets/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP completely duplicate packets',
#             'groups': groups
#          },#
#          {
#             'name': NAME_PREFIX + 'tcp_out_of_order_bytes',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'bytes/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP out-of-order bytes',
#             'groups': groups
#          },#
#          {
#             'name': NAME_PREFIX + 'tcp_out_of_order_packets',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'packets/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP out-of-order packets',
#             'groups': groups
#          },#
#          {
#             'name': NAME_PREFIX + 'tcp_window_update_packets',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'packets/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP window update packets',
#             'groups': groups
#          },
#          {
#             'name': NAME_PREFIX + 'tcp_memory_problem_packets',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'packets/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP discarded packets due to memory problems',
#             'groups': groups
#          },
#          {
#             'name': NAME_PREFIX + 'tcp_connection_requests',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'requests/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP connection requests',
#             'groups': groups
#          },
#          {
#             'name': NAME_PREFIX + 'tcp_bad_connection_attempts',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'attempts/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP bad connection attempts',
#             'groups': groups
#          },
#          {
#             'name': NAME_PREFIX + 'tcp_connections_established',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'connections/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP connections established',
#             'groups': groups
#          },
#          {
#             'name': NAME_PREFIX + 'tcp_connections_closed',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'connections/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP connections closed',
#             'groups': groups
#          },
#          {
#             'name': NAME_PREFIX + 'tcp_embryonic_connections_dropped',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'connections/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP embryonic connection dropped',
#             'groups': groups
#          },
#          {
#             'name': NAME_PREFIX + 'tcp_connections_dropped_timeout',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'connections/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP Connections (fin_wait_2) dropped because of timeout',
#             'groups': groups
#          },
#          {
#             'name': NAME_PREFIX + 'tcp_ack_predictions',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'ACKs/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP correct ACK header predictions',
#             'groups': groups
#          },
#          {
#             'name': NAME_PREFIX + 'tcp_data_predictions',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'packets/sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'TCP correct data packet header predictions',
#             'groups': groups
#          }#,
        {
            'name': NAME_PREFIX + 'outliers',
            'call_back': get_value,
            'time_max': time_max,
            'value_type': 'uint',
            'units': 'Outliers/Violations (99th)',
            'slope': 'both',
            'format': '%d',
            'description': 'Outliers(last 20samp.)',
            'groups': groups
        },
        {
            'name': NAME_PREFIX + 'death',
            'call_back': get_value,
            'time_max': time_max,
            'value_type': 'uint',
            'units': 'Yes: 1/ No: 0',
            'slope': 'both',
            'format': '%d',
            'description': 'Workload death',
            'groups': groups
        },
        {
            'name': NAME_PREFIX + 'violation',
            'call_back': get_value,
            'time_max': time_max,
            'value_type': 'uint',
            'units': 'Yes: 1/ No: 0',
            'slope': 'both',
            'format': '%d',
            'description': 'SLO violation',
            'groups': groups
        },
        {
            'name': NAME_PREFIX + 'throughput',
            'call_back': get_value,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'Operations/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'Throughput',
            'groups': groups
        },
        {
            'name': NAME_PREFIX + 'rtt',
            'call_back': get_value,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'milliseconds',
            'slope': 'both',
            'format': '%f',
            'description': 'RTT to WL Target',
            'groups': groups
        },
        {
            'name': NAME_PREFIX + 'service_rtt',
            'call_back': get_value,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'milliseconds',
            'slope': 'both',
            'format': '%f',
            'description': 'RTT to service port',
            'groups': groups
        },
        {
            'name': NAME_PREFIX + 'latency_99th',
            'call_back': get_value,
            'time_max': time_max,
            'value_type': 'uint',
            'units': 'milliseconds',
            'slope': 'both',
            'format': '%d',
            'description': '99th percentile latency',
            'groups': groups
        },
        {
            'name': NAME_PREFIX + 'latency_95th',
            'call_back': get_value,
            'time_max': time_max,
            'value_type': 'uint',
            'units': 'milliseconds',
            'slope': 'both',
            'format': '%d',
            'description': '95th percentile latency',
            'groups': groups
        },
        {
            'name': NAME_PREFIX + 'target_throughput',
            'call_back': get_value,
            'time_max': time_max,
            'value_type': 'uint',
            'units': 'Operations/sec',
            'slope': 'both',
            'format': '%d',
            'description': 'Target throughput',
            'groups': groups
        },
        {
            'name': NAME_PREFIX + 'max_latency_avg',
            'call_back': get_value,
            'time_max': time_max,
            'value_type': 'uint',
            'units': 'milliseconds',
            'slope': 'both',
            'format': '%d',
            'description': 'Max. latency average',
            'groups': groups
        },
        {
            'name': NAME_PREFIX + 'latency_avg',
            'call_back': get_value,
            'time_max': time_max,
            'value_type': 'uint',
            'units': 'milliseconds',
            'slope': 'both',
            'format': '%d',
            'description': 'Latency average',
            'groups': groups
        },
        {
            'name': NAME_PREFIX + 'max_latency_99th',
            'call_back': get_value,
            'time_max': time_max,
            'value_type': 'uint',
            'units': 'milliseconds',
            'slope': 'both',
            'format': '%d',
            'description': 'Max. 99th percentile latency',
            'groups': groups
        },
        {
            'name': NAME_PREFIX + 'max_latency_95th',
            'call_back': get_value,
            'time_max': time_max,
            'value_type': 'uint',
            'units': 'milliseconds',
            'slope': 'both',
            'format': '%d',
            'description': 'Max. 95th percentile latency',
            'groups': groups
        },
        {
            'name': NAME_PREFIX + 'system_id',
            'call_back': get_value,
            'time_max': time_max,
            'value_type': 'uint',
            'units': 'identifier',
            'slope': 'both',
            'format': '%d',
            'description': 'System id.',
            'groups': groups
        }#,
#         {
#             'name': NAME_PREFIX + 'mem_virtual',
#             'call_back': get_value,
#             'time_max': time_max,
#             'value_type': 'uint',
#             'units': 'MB',
#             'slope': 'both',
#             'format': '%u',
#             'description': 'Process Virtual Size',
#             'groups': groups
#         },
#         {
#             'name': NAME_PREFIX + 'mem_resident',
#             'call_back': get_value,
#             'time_max': time_max,
#             'value_type': 'uint',
#             'units': 'MB',
#             'slope': 'both',
#             'format': '%u',
#             'description': 'Process Resident Size',
#             'groups': groups
#         },
#         {
#             'name': NAME_PREFIX + 'extra_info_page_faults',
#             'call_back': get_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'Faults/Sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'Page Faults',
#             'groups': groups
#         },
#         {
#             'name': NAME_PREFIX + 'globalLock_ratio',
#             'call_back': get_globalLock_ratio,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': '%',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'Global Write Lock Ratio',
#             'groups': groups
#         },
#         {
#             'name': NAME_PREFIX + 'indexCounters_btree_miss_ratio',
#             'call_back': get_indexCounters_btree_miss_ratio,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': '%',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'BTree Page Miss Ratio',
#             'groups': groups
#         },
#         {
#             'name': NAME_PREFIX + 'globalLock_currentQueue_total',
#             'call_back': get_value,
#             'time_max': time_max,
#             'value_type': 'uint',
#             'units': 'Operations',
#             'slope': 'both',
#             'format': '%u',
#             'description': 'Total Operations Waiting for Lock',
#             'groups': groups
#         },
#         {
#             'name': NAME_PREFIX + 'globalLock_currentQueue_readers',
#             'call_back': get_value,
#             'time_max': time_max,
#             'value_type': 'uint',
#             'units': 'Operations',
#             'slope': 'both',
#             'format': '%u',
#             'description': 'Readers Waiting for Lock',
#             'groups': groups
#         },
#         {
#             'name': NAME_PREFIX + 'globalLock_currentQueue_writers',
#             'call_back': get_value,
#             'time_max': time_max,
#             'value_type': 'uint',
#             'units': 'Operations',
#             'slope': 'both',
#             'format': '%u',
#             'description': 'Writers Waiting for Lock',
#             'groups': groups
#         },
#         {
#             'name': NAME_PREFIX + 'globalLock_activeClients_total',
#             'call_back': get_value,
#             'time_max': time_max,
#             'value_type': 'uint',
#             'units': 'Clients',
#             'slope': 'both',
#             'format': '%u',
#             'description': 'Total Active Clients',
#             'groups': groups
#         },
#         {
#             'name': NAME_PREFIX + 'globalLock_activeClients_readers',
#             'call_back': get_value,
#             'time_max': time_max,
#             'value_type': 'uint',
#             'units': 'Clients',
#             'slope': 'both',
#             'format': '%u',
#             'description': 'Active Readers',
#             'groups': groups
#         },
#         {
#             'name': NAME_PREFIX + 'globalLock_activeClients_writers',
#             'call_back': get_value,
#             'time_max': time_max,
#             'value_type': 'uint',
#             'units': 'Clients',
#             'slope': 'both',
#             'format': '%u',
#             'description': 'Active Writers',
#             'groups': groups
#         },
#         {
#             'name': NAME_PREFIX + 'connections_current',
#             'call_back': get_value,
#             'time_max': time_max,
#             'value_type': 'uint',
#             'units': 'Connections',
#             'slope': 'both',
#             'format': '%u',
#             'description': 'Open Connections',
#             'groups': groups
#         },
#         {
#             'name': NAME_PREFIX + 'connections_current_ratio',
#             'call_back': get_connections_current_ratio,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': '%',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'Percentage of Connections Used',
#             'groups': groups
#         },
#         {
#             'name': NAME_PREFIX + 'slave_delay',
#             'call_back': get_slave_delay,
#             'time_max': time_max,
#             'value_type': 'uint',
#             'units': 'Seconds',
#             'slope': 'both',
#             'format': '%u',
#             'description': 'Replica Set Slave Delay',
#             'groups': groups
#         },
#         {
#             'name': NAME_PREFIX + 'asserts_total',
#             'call_back': get_asserts_total_rate,
#             'time_max': time_max,
#             'value_type': 'float',
#             'units': 'Asserts/Sec',
#             'slope': 'both',
#             'format': '%f',
#             'description': 'Asserts',
#             'groups': groups
#         }
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
