import rrdtool
import glob
import sys
from configobj import ConfigObj
import socket
import subprocess
import filecmp

#db api available in home_dir
conf_file = "/etc/svc.conf"
config=ConfigObj(conf_file)
sys.path.append(config['home_dir'])
ALIVE_TIME=int(config['alive_time'])

rrd_path_vms_prefix=config['rrd_path_vms_prefix']
subprocess.Popen(["cp", "/etc/hosts", "/tmp/hosts.last"], stdout=subprocess.PIPE,close_fds=True)
subprocess.Popen(["sudo","cp", "/etc/hosts.default", "/etc/hosts"], stdout=subprocess.PIPE,close_fds=True)
for filename in (sorted(glob.glob(rrd_path_vms_prefix+"/*"))):
    try:
        info =  (filename).split('/')[-1]
        socket.inet_aton(info)
        #print info
        script_to_run=config['home_dir']+"/svc/common/deployment/fix_hosts.sh"
        script_out=subprocess.Popen(["sh",script_to_run,info], stdout=subprocess.PIPE,close_fds=True).communicate()[0].rstrip()
        #print script_out
    except socket.error:
        None

if not (filecmp.cmp('/etc/hosts', '/tmp/hosts.last')):
    subprocess.Popen(["sudo","service", "ganglia-monitor","restart"], stdout=subprocess.PIPE,close_fds=True)
    subprocess.Popen(["sudo","service", "gmetad","restart"], stdout=subprocess.PIPE,close_fds=True)

sys.exit(0)
#print "isso"