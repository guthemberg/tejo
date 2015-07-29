from pymongo import MongoClient
#from configobj import ConfigObj
import sys, getopt
from time import sleep


def compute_args(argv):
   db = ''
   collection=''
   host=''
   
   try:
       opts, args = getopt.getopt(argv,"hd:c:n:",["db=","collection=","host="])
   except getopt.GetoptError:
       print 'setup_sharding.py -d <db_name> -c <collection_name> -n <host>'
       sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'setup_sharding.py -d <db_name> -c <collection_name> -n <host>'
         sys.exit()
      elif opt in ("-d", "--db"):
         db = arg
      elif opt in ("-c", "--collection"):
         collection = arg
      elif opt in ("-n", "--host"):
         host = arg
   if len(db)==0 or len(collection)==0 or len(host)==0:
       print 'setup_sharding.py -d <db_name> -c <collection_name> -n <host>'
       sys.exit(2)
   return (db,collection,host)

def wait_awhile():   
    print "waiting 60 seconds before continuing..."
    sleep(60)
    print "done."
    
def main(argv):
    (db,collection,host)=compute_args(argv)
    
    c = MongoClient(host, 27017)
    c.admin.command({"enableSharding": db})
    wait_awhile()
    #sh.shardCollection("ycsb.usertable", { "_id": "hashed" } )
    #db.runCommand( { shardCollection: "records.people", key: { zipcode: 1 } } )
    db_collection="%s.%s" % (db,collection)
    c.admin.command({ 'shardCollection': db_collection, 'key': { "_id": "hashed" } })
    wait_awhile()
    wait_awhile()
    

if __name__ == "__main__":
   main(sys.argv[1:])

