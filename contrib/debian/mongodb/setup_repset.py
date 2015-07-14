from pymongo import MongoClient
#from configobj import ConfigObj
import sys, getopt
from time import sleep


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

def wait_awhile():   
    print "waiting 60 seconds before continuing..."
    sleep(60)
    print "done."
    
def main(argv):
    (rset,vms,arbiter)=compute_args(argv)
    
    hosts=[]
    id=0
    c = MongoClient('localhost', 27017)
    for hostname in vms.split(','):
        host="%s:27017" % hostname
        #maximum number of voting members, as described in
        #http://docs.mongodb.org/manual/tutorial/expand-replica-set/
        if id<7:
            hosts.append({'_id': id, 'host': host})
        else:
            hosts.append({'_id': id, 'host': host,'votes': 0})

        version=id+1
        config={'_id': rset, 'version':version, 'members': hosts}
        if id==0:
            c.admin.command("replSetInitiate", config)
            wait_awhile()
        else:
            c.admin.command("replSetReconfig",config) 
            wait_awhile()
        id=id+1
    #arbiter
    host="%s:30000" % arbiter
    hosts.append({'_id': id,'host': host,"arbiterOnly" : True,'votes': 0})
    version=id+1
    config={'_id': rset, 'version':version, 'members': hosts}
    c.admin.command("replSetReconfig",config)
    #conf_file = "/etc/tejo.conf"
    #config=ConfigObj(conf_file)
    

if __name__ == "__main__":
   main(sys.argv[1:])

