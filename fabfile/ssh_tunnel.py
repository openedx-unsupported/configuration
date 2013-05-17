from fabric.api import abort, env, fastprint
from fabric.colors import green, red, white
import subprocess
import shlex
import atexit
import time
import boto
import re
import socket

DOMAIN = 'm.edx.org:22'


class SSHTunnel:

    port = 9000  # default starting port
    tunnels = {}

    def __init__(self, host, phost, user, lport=None):

        if lport is not None:
            SSHTunnel.port = lport

        while True:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            try:
                s.connect(('localhost', SSHTunnel.port))
                s.shutdown(2)
                # connection was successful so try a new port
                SSHTunnel.port += 1
            except:
                self.lport = SSHTunnel.port
                break
        phost = re.sub(':(\d+)', r' -p\1 ', phost)

        identities = ''
        if env.key_filename:
            # could be a list or a string
            if isinstance(env.key_filename, basestring):
                lst = [env.key_filename]
            else:
                lst = env.key_filename

            identities = ' '.join('-i {f} '.format(f=f) for f in lst)

        cmd = 'ssh -o UserKnownHostsFile=/dev/null ' \
              '{ids}' \
              '-o StrictHostKeyChecking=no -vAN -L {lport}:{host} ' \
              '{user}@{phost}'.format(ids=identities, lport=self.lport,
                                      host=host, user=user, phost=phost)

        self.p = subprocess.Popen(shlex.split(cmd),
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)

        start_time = time.time()
        atexit.register(self.p.kill)
        while not 'Entering interactive session' in self.p.stderr.readline():
            if time.time() > start_time + 10:
                abort(red("Unable to create ssh tunnel - `{0}`".format(cmd)))

    def local(self):
        return 'localhost:{lport}'.format(lport=self.lport)


def setup_tunnel(all_hosts, check_tag=True,
                 proxy_name=None, user=None, lport=None):
    """
    Given a all_hosts it will check to see whether
    any are proxy hosts if check_tag is True

    returns a modified list
    of hosts with localhost:port for tunneled hosts.
    """

    if user is None:
        user = env.user
    ec2 = boto.connect_ec2()

    # the proxy hosts
    proxies = {}
    if check_tag:
        for res in ec2.get_all_instances(filters={'tag-key': 'proxy'}):
            for inst in res.instances:
                host = ".".join([inst.tags['Name'], DOMAIN])
                proxy = ".".join([inst.tags['proxy'], DOMAIN])
                proxies.update({host: proxy})
    else:
        if not proxy_name:
            raise Exception("Must specify a proxy_host")

        proxies = {host: proxy_name for host in all_hosts}

    # local tunneling ip:port
    tunnels = {}
    for host in all_hosts:
        if host in proxies and host not in SSHTunnel.tunnels:
            t = SSHTunnel(host=host, phost=proxies[host],
                          user=user, lport=lport)
            tunnels[host] = t.local()
            fastprint(green('created {0} for {1} via {2}'.format(tunnels[host],
                      host, proxies[host])) + white('\n'))
            SSHTunnel.tunnels.update(tunnels)

    return([SSHTunnel.tunnels[host] if host in SSHTunnel.tunnels else host
           for host in all_hosts])
