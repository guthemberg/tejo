import glob
from configobj import ConfigObj

SVC_CONF_FILE="/etc/svc.conf"

config=ConfigObj(SVC_CONF_FILE)
hostname=config["vms"][0]
rrd_path_vms_prefix=config["rrd_path_vms_prefix"]
keys= [ (( (filename).split("/")[-1] ).split(".")[0]) for filename in (sorted(glob.glob(rrd_path_vms_prefix+"/"+hostname+"/*.rrd")))]
print ",".join(keys)