#!/usr/bin/python

import argparse
import subprocess

parser=argparse.ArgumentParser(description='Shovels between RabbitMQ Clusters')
parser.add_argument('--src_host',action='store',dest='src_host')
parser.add_argument('--dest_host',action='store',dest='dest_host',default='127.0.0.1')
parser.add_argument('--src_user',action='store',dest='src_user')
parser.add_argument('--dest_user',action='store',dest='dest_user')
parser.add_argument('--src_pass',action='store',dest='src_pass')
parser.add_argument('--dest_pass',action='store',dest='dest_pass')
parser.add_argument('--src_queue',action='store',dest='src_queue')
parser.add_argument('--dest_queue',action='store',dest='dest_queue')
parser.add_argument('--name',action='store',dest='name')

args=parser.parse_args()

SRC_URI="\"amqp://%s:%s@%s\"" % (args.src_user,args.src_pass,args.src_host)
DEST_URI="\"amqp://%s:%s@%s\"" % (args.dest_user,args.dest_pass,args.dest_host)
SRC_QUEUE="\"%s\"" % args.src_queue
DEST_QUEUE="\"%s\"" % args.dest_queue
SHOVEL_NAME="%s" % args.name
SHOVEL_ARGS="{\"src-uri\": %s, \"src-queue\": %s,\"dest-uri\": %s,\"dest-queue\": %s}" % (SRC_URI,SRC_QUEUE,DEST_URI,DEST_QUEUE)

def run_cmd(cmd):
    subprocess.call(cmd,shell=True)

if __name__=='__main__':

    create_shovel="/usr/sbin/rabbitmqctl set_parameter shovel %s '%s'" % \
                  (SHOVEL_NAME,SHOVEL_ARGS)
    ''' 
    command line arguments are expected to be in following format
    python shovel.py --name <<shovel_name>> --src_user <<src_rabbitmq_user>> --src_pass <<user_pass>> \
    --src_host <<src_host_IP>> --src_queue <<src_queue_name>> --dest_user <<dest_rabbitmq_user>> --dest_pass <<user_pass>> \
    --dest_host <<dest_host_IP>> --dest_queue <<dest_queue>> 
    '''
    run_cmd(create_shovel)
