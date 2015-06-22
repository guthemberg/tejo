from pymongo import MongoClient
#from configobj import ConfigObj
import sys, getopt


def compute_args(argv):
   rset = ''
   vms = ''
   
   try:
       opts, args = getopt.getopt(argv,"hn:v:",["rset=","vms="])
   except getopt.GetoptError:
       print 'setup_repset.py -n <rep_set> -v <vm1,vm2,...>'
       sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'setup_repset.py -n <rep_set> -v <vm1,vm2,...>'
         sys.exit()
      elif opt in ("-n", "--rset"):
         rset = arg
      elif opt in ("-v", "--vms"):
         vms = arg
   if len(rset)==0 or len(vms)==0:
       print 'setup_repset.py -n <rep_set> -v <vm1,vm2,...>'
       sys.exit(2)
   return (rset,vms)
   
def main(argv):
    (rset,vms)=compute_args(argv)
    
    hosts=[]
    id=0
    for hostname in vms.split(','):
        host="%s:27017" % hostname
        hosts.append({'_id': id, 'host': host})
        id=id+1
    print hosts
    config={'_id': rset, 'members': hosts}
    c = MongoClient('localhost', 27017)
    c.admin.command("replSetInitiate", config)
    #conf_file = "/etc/tejo.conf"
    #config=ConfigObj(conf_file)
    

if __name__ == "__main__":
   main(sys.argv[1:])

