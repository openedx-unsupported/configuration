#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function
import argparse
import subprocess
import requests
from requests.exceptions import HTTPError
import sys
import six

parser=argparse.ArgumentParser(description='Shovels between RabbitMQ Clusters')
parser.add_argument('--src_host',action='store',dest='src_host')
parser.add_argument('--dest_host',action='store',dest='dest_host',default='127.0.0.1')
parser.add_argument('--src_user',action='store',dest='src_user')
parser.add_argument('--src_user_pass',action='store',dest='src_user_pass')
parser.add_argument('--dest_user',action='store',dest='dest_user')
parser.add_argument('--dest_user_pass',action='store',dest='dest_user_pass')

args=parser.parse_args()

src_uri='amqp://{}:{}@{}'.format(args.src_user,args.src_user_pass,args.src_host)
dest_uri='amqp://{}:{}@{}'.format(args.dest_user,args.dest_user_pass,args.dest_host)
port=15672

def list_vhosts():
    url='http://{}:{}/api/vhosts'.format(args.src_host,port)
    try:
        response=requests.get(url,auth=(args.src_user,args.src_user_pass))
        response.raise_for_status()
        vhosts=[v['name'] for v in response.json() if v['name'].startswith('/')]
    except Exception as ex:
        print("Failed to get vhosts: {}".format(ex))
        sys.exit(1)
    return vhosts

def list_queues():
    for vhost in list_vhosts():
        url='http://{}:{}/api/queues/{}'.format(args.src_host,port,vhost)
        try:
            response=requests.get(url,auth=(args.src_user,args.src_user_pass))
            response.raise_for_status()
            queues=[q['name'] for q in response.json()]
        except Exception as ex:
            print("Failed to get queues: {}".format(ex))
            sys.exit(1)
        return queues

def create_shovel(shovel,arg):
    cmd="/usr/sbin/rabbitmqctl set_parameter shovel {} '{}'".format(shovel,arg)
    try:
        subprocess.check_output(
                              cmd,stderr=subprocess.STDOUT,shell=True)
    except subprocess.CalledProcessError as ex:
        return ex.output

if __name__=='__main__':

    """
    command line arguments are expected to be in following format
    python shovel.py --src_host <src_host_IP> --src_user <src_rabbitmq_user> --src_user_pass <user_pass>  \
    --dest_host <dest_host_IP> --dest_user <dest_rabbitmq_user> --dest_user_pass <user_pass>
    """
    output={}    
    for queue in list_queues():
        """ 
        Ignore queues celeryev and *.pidbox to shovel
        """
        q=queue.split('.')
        if (q[0]!='celeryev' and q[-1]!='pidbox'):
            args='{{"src-uri": "{}", "src-queue": "{}","dest-uri": "{}","dest-queue": "{}"}}'.format(src_uri,queue,dest_uri,queue)
            print("Running shovel for queue:{}".format(queue))
            shovel_output=create_shovel(queue,args)
            if shovel_output is not None:
               content=six.text_type(shovel_output,"utf-8")
               output[queue]=content
    for k,v in output.items():
          print(k,v)
