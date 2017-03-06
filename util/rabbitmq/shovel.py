import argparse
import subprocess
import requests

parser=argparse.ArgumentParser(description='Shovels between RabbitMQ Clusters')
parser.add_argument('--src_host',action='store',dest='src_host')
parser.add_argument('--dest_host',action='store',dest='dest_host',default='127.0.0.1')
parser.add_argument('--src_user',action='store',dest='src_user')
parser.add_argument('--src_user_pass',action='store',dest='src_user_pass')
parser.add_argument('--dest_user',action='store',dest='dest_user')
parser.add_argument('--dest_user_pass',action='store',dest='dest_user_pass')

args=parser.parse_args()

src_uri="\"amqp://%s:%s@%s\"" % (args.src_user,args.src_user_pass,args.src_host)
dest_uri="\"amqp://%s:%s@%s\"" % (args.dest_user,args.dest_user_pass,args.dest_host)
port=15672

def list_vhosts():
    url="http://%s:%d/api/vhosts" % (args.src_host,port)
    response=requests.get(url,auth=(args.src_user,args.src_user_pass))
    vhosts=[v['name'] for v in response.json() if v['name'].startswith('/')]
    return vhosts

def list_queues():
    for vhost in list_vhosts():
        url="http://%s:%d/api/queues/%s" % (args.src_host,port,vhost)
        response=requests.get(url,auth=(args.src_user,args.src_user_pass))
        queues=[q['name'] for q in response.json()]
        return queues

def create_shovel(shovel,arg):
    cmd="/usr/sbin/rabbitmqctl set_parameter shovel %s '%s'" % (shovel,arg)
    subprocess.call(
                cmd,shell=True)

if __name__=='__main__':

    """
    command line arguments are expected to be in following format
    python shovel.py --src_host <src_host_IP> --src_user <src_rabbitmq_user> --src_user_pass <user_pass>  \
    --dest_host <dest_host_IP> --dest_user <dest_rabbitmq_user> --dest_user_pass <user_pass>
    """
        
    for queue in list_queues():
        """ 
        Ignore queues celeryev and *.pidbox to shovel
        """
        q=queue.split('.')
        if (q[0]!='celeryev' and q[-1]!='pidbox'):
            args="{\"src-uri\": %s, \"src-queue\": \"%s\",\"dest-uri\": %s,\"dest-queue\": \"%s\"}" % (src_uri,queue,dest_uri,queue)
            create_shovel(queue,args)
