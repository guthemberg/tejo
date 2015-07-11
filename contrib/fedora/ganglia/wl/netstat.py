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

import os
import socket
import time
import copy

NAME_PREFIX = 'netstat_'
PARAMS = {
    'net_status' : '/usr/bin/netstat -s -p tcp'
}
METRICS = {
    'time' : 0,
    'data' : {}
}
LAST_METRICS = copy.deepcopy(METRICS)
METRICS_CACHE_TTL = 3



def get_metrics():
    """Return all metrics"""

    global METRICS, LAST_METRICS

    if (time.time() - METRICS['time']) > METRICS_CACHE_TTL:

        metrics = {}
        for status_type in PARAMS.keys():

            # get raw metric data
            io = os.popen(PARAMS[status_type])

            # clean up
            
            for row in (''.join(io.readlines()).strip()).split('\n'):
                if 'bytes) retransmitted' in row:
                    metrics['tcp_retransmitted_packets']=float((row.split('data')[0]))
                    metrics['tcp_retransmitted_bytes']=float((row.split('(')[1]).split(' ')[0])
                elif 'ack-only packets' in row:
                    metrics['tcp_ack_only_packets']=float((row.split('ack')[0]))
                elif 'control packets' in row:
                    metrics['tcp_control_packets']=float((row.split('control')[0]))
                elif 'acks (for' in row:
                    metrics['tcp_acks_bytes']=float((row.split('for')[1]).split('bytes')[0])
                    metrics['tcp_acks_packets']=float((row.split('acks')[0]))
                elif 'duplicate acks' in row:
                    metrics['tcp_duplicate_acks']=float((row.split('duplicate')[0]))
                elif 'received in-sequence' in row:
                    metrics['tcp_received_in_sequence_bytes']=float((row.split('(')[1]).split(' ')[0])
                    metrics['tcp_received_in_sequence_packets']=float((row.split('packets')[0]))
                elif 'completely' in row:
                    metrics['tcp_completely_duplicate_bytes']=float((row.split('(')[1]).split(' ')[0])
                    metrics['tcp_completely_duplicate_packets']=float((row.split('completely')[0]))
                elif 'out-of-order' in row:
                    metrics['tcp_out_of_order_bytes']=float((row.split('(')[1]).split(' ')[0])
                    metrics['tcp_out_of_order_packets']=float((row.split('out-of-order')[0]))
                elif 'window update' in row:
                    if 'tcp_window_update_packets' in metrics.keys():
                        metrics['tcp_window_update_packets']=metrics['tcp_window_update_packets']+float((row.split('window')[0]))
                    else:
                        metrics['tcp_window_update_packets']=float((row.split('window')[0]))
                elif 'memory' in row:
                    metrics['tcp_memory_problem_packets']=float((row.split('discarded')[0]))
                elif 'requests' in row:
                    metrics['tcp_connection_requests']=float((row.split('connection')[0]))
                elif 'bad connection' in row:
                    metrics['tcp_bad_connection_attempts']=float((row.split('bad')[0]))
                elif 'established' in row:
                    metrics['tcp_connections_established']=float((row.split('connections')[0]))
                elif 'closed' in row:
                    metrics['tcp_connections_closed']=float((row.split('connections')[0]))
                elif 'embryonic' in row:
                    metrics['tcp_embryonic_connections_dropped']=float((row.split('embryonic')[0]))
                elif 'fin_wait_2' in row:
                    metrics['tcp_connections_dropped_timeout']=float((row.split('Connections')[0]))
                elif 'correct ACK' in row:
                    metrics['tcp_ack_predictions']=float((row.split('correct')[0]))
                elif 'correct data' in row:
                    metrics['tcp_data_predictions']=float((row.split('correct')[0]))
                
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
    groups = 'netstat'
    descriptors = [
        {
            'name': NAME_PREFIX + 'tcp_retransmitted_bytes',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'bytes/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP retransmitted bytes',
            'groups': groups
        },
        {
            'name': NAME_PREFIX + 'tcp_retransmitted_packets',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'packets/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP retransmitted packets',
            'groups': groups
        },#
        {
            'name': NAME_PREFIX + 'tcp_control_packets',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'packets/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP control packets',
            'groups': groups
        },
         {
             'name': NAME_PREFIX + 'tcp_ack_only_packets',
             'call_back': get_rate,
             'time_max': time_max,
             'value_type': 'float',
             'units': 'packets/sec',
             'slope': 'both',
             'format': '%f',
             'description': 'TCP ack-only packets',
             'groups': groups
         },
         {
            'name': NAME_PREFIX + 'tcp_acks_bytes',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'bytes/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP acks bytes',
            'groups': groups
         },
         {
            'name': NAME_PREFIX + 'tcp_acks_packets',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'packets/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP ACKs packets',
            'groups': groups
         },#
         {
            'name': NAME_PREFIX + 'tcp_duplicate_acks',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'acks/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP duplicate acks',
            'groups': groups
         },
         {
            'name': NAME_PREFIX + 'tcp_received_in_sequence_bytes',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'bytes/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP received in-sequence bytes',
            'groups': groups
         },
         {
            'name': NAME_PREFIX + 'tcp_received_in_sequence_packets',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'packets/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP received in-sequence packets',
            'groups': groups
         },#
         {
            'name': NAME_PREFIX + 'tcp_completely_duplicate_bytes',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'bytes/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP completely duplicate bytes',
            'groups': groups
         },#
         {
            'name': NAME_PREFIX + 'tcp_completely_duplicate_packets',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'packets/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP completely duplicate packets',
            'groups': groups
         },#
         {
            'name': NAME_PREFIX + 'tcp_out_of_order_bytes',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'bytes/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP out-of-order bytes',
            'groups': groups
         },#
         {
            'name': NAME_PREFIX + 'tcp_out_of_order_packets',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'packets/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP out-of-order packets',
            'groups': groups
         },#
         {
            'name': NAME_PREFIX + 'tcp_window_update_packets',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'packets/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP window update packets',
            'groups': groups
         },
         {
            'name': NAME_PREFIX + 'tcp_memory_problem_packets',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'packets/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP discarded packets due to memory problems',
            'groups': groups
         },
         {
            'name': NAME_PREFIX + 'tcp_connection_requests',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'requests/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP connection requests',
            'groups': groups
         },
         {
            'name': NAME_PREFIX + 'tcp_bad_connection_attempts',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'attempts/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP bad connection attempts',
            'groups': groups
         },
         {
            'name': NAME_PREFIX + 'tcp_connections_established',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'connections/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP connections established',
            'groups': groups
         },
         {
            'name': NAME_PREFIX + 'tcp_connections_closed',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'connections/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP connections closed',
            'groups': groups
         },
         {
            'name': NAME_PREFIX + 'tcp_embryonic_connections_dropped',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'connections/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP embryonic connection dropped',
            'groups': groups
         },
         {
            'name': NAME_PREFIX + 'tcp_connections_dropped_timeout',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'connections/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP Connections (fin_wait_2) dropped because of timeout',
            'groups': groups
         },
         {
            'name': NAME_PREFIX + 'tcp_ack_predictions',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'ACKs/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP correct ACK header predictions',
            'groups': groups
         },
         {
            'name': NAME_PREFIX + 'tcp_data_predictions',
            'call_back': get_rate,
            'time_max': time_max,
            'value_type': 'float',
            'units': 'packets/sec',
            'slope': 'both',
            'format': '%f',
            'description': 'TCP correct data packet header predictions',
            'groups': groups
         }#,
#         {
#             'name': NAME_PREFIX + 'mem_mapped',
#             'call_back': get_value,
#             'time_max': time_max,
#             'value_type': 'uint',
#             'units': 'MB',
#             'slope': 'both',
#             'format': '%u',
#             'description': 'Memory-mapped Data',
#             'groups': groups
#         },
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
