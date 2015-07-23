import os
import psutil
import sys

PROCESS = psutil.Process(os.getpid())
MEGA = 10 ** 6
MEGA_STR = ' ' * MEGA

from time import sleep

def get_available_memory():
    return psutil.avail_phymem()
    
# def pmem():
#     tot=psutil.TOTAL_PHYMEM
#     avail=psutil.avail_phymem()
#     percent=psutil.virtual_memory().percent
#     used=psutil.virtual_memory().used
#     free = psutil.virtual_memory().free
#     tot, avail, used, free = tot / MEGA, avail / MEGA, used / MEGA, free / MEGA
#     proc = PROCESS.get_memory_info()[1] / MEGA
#     print('process = %s total = %s avail = %s used = %s free = %s percent = %s'
#           % (proc, tot, avail, used, free, percent))
# 
# def alloc_max_array():
#     print "allocating string"
#     i = 0
#     ar = []
#     while True:
#         try:
#             #ar.append(MEGA_STR)  # no copy if reusing the same string!
#             ar.append(MEGA_STR + str(i))
#         except MemoryError:
#             break
#         i += 1
#         print "step: %d" % i
#         if i==10:
#             print "sleeping 120"
#             sleep(120)
#             break
#     max_i = i - 1
#     print 'maximum array allocation:', max_i
#     pmem()
    
def memory_usage_psutil():
    # return the memory usage in MB
    process = psutil.Process(os.getpid())
    mem = process.get_memory_info()[0] / float(2 ** 20)
    return mem

def alloc_max_str(proportion=0.3,duration=3600):
    FACTOR=128
    ratio=(float(psutil.TOTAL_PHYMEM)*proportion) / float(2 ** 20)
    i=int((float(psutil.TOTAL_PHYMEM)*proportion)/(FACTOR * MEGA))
    #print ratio
    while True:
        try:
            a = ' ' * (i * FACTOR * MEGA)
            print "step: %d" % i
            if memory_usage_psutil()>=ratio:
                #print memory_usage_psutil()
                #print "sleeping 120"
                sleep(duration)
                break
            del a
        except MemoryError:
            break
        i += 1
    max_i = i - 1
    _ = ' ' * (max_i * FACTOR * MEGA)

    #print 'maximum string allocation', max_i
    #pmem()


alloc_max_str(proportion=float(sys.argv[1]),duration=int(sys.argv[2]))
sys.exit(0)
# print sys.argv[1]
# print sys.argv[2]
# sys.exit()
# pmem()
# ratio=get_available_memory()*.25
# print ratio
# #sys.exit()
# alloc_max_str()
#alloc_max_array()
