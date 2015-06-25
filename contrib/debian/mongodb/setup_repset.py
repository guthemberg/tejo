from pymongo import MongoClient
#from configobj import ConfigObj
import sys, getopt


def compute_args(argv):
   rset = ''
   vms = ''
   arbiter=''
   
   try:
       opts, args = getopt.getopt(argv,"hn:v:a:",["rset=","vms=","arbiter="])
   except getopt.GetoptError:
       print 'setup_repset.py -n <rep_set> -v <vm1,vm2,...> -a arbiter'
       sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'setup_repset.py -n <rep_set> -v <vm1,vm2,...> -a arbiter'
         sys.exit()
      elif opt in ("-n", "--rset"):
         rset = arg
      elif opt in ("-v", "--vms"):
         vms = arg
      elif opt in ("-a", "--arbiter"):
         arbiter = arg
   if len(rset)==0 or len(vms)==0 or len(arbiter)==0:
       print 'setup_repset.py -n <rep_set> -v <vm1,vm2,...> -a arbiter'
       sys.exit(2)
   return (rset,vms,arbiter)
   
def main(argv):
    (rset,vms,arbiter)=compute_args(argv)
    
    hosts=[]
    id=0
    for hostname in vms.split(','):
        host="%s:27017" % hostname
        hosts.append({'_id': id, 'host': host})
        id=id+1
    #arbiter
    host="%s:30000" % arbiter
    hosts.append({'_id': id, 'host': host,"arbiterOnly" : True})
    config={'_id': rset, 'members': hosts}
    c = MongoClient('localhost', 27017)
    c.admin.command("replSetInitiate", config)
    #conf_file = "/etc/tejo.conf"
    #config=ConfigObj(conf_file)
    

if __name__ == "__main__":
   main(sys.argv[1:])

