#!/usr/bin/python

"""Custom topology

N hosts directly connected to one switch

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

import sys
import time
import subprocess
from itertools import combinations
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.util import dumpNodeConnections
from mininet.util import dumpNetConnections

class simple_topo( Topo ):
    "Simple topology example."

    def build( self: Topo, n: int = 2 ):
        "Create custom topo."

        # Add switch
        switch = self.addSwitch( 's1' )

        # Add hosts with links connecting to switch
        for i in range(n):
            host = self.addHost( 'h{}'.format(i + 1) )
            self.addLink( host, switch, bw=1000, delay='0ms', loss=0, max_queue_size=99999 )

def make_switch_traditional(net: Mininet, switch: str):
    net[switch].cmd('ovs-ofctl add-flow {} action=normal'.format(switch))

def dump_switch_information(net: Mininet, switch: str):
    print( "Dumping switch information w/ ovs-ofctl" )
    print(net[switch].cmd('ovs-ofctl show {}'.format(switch)))

def dump_switch_flows(net: Mininet, switch: str):
    print( "Dumping flow rules on {}".format(switch) )
    print(net[switch].cmd('ovs-ofctl dump-flows {}'.format(switch)))

def dump_infos(net: Mininet):
    print( "Dumping host connections" )
    dumpNodeConnections(net.hosts)
    print( "Dumping switch connections" )
    dumpNodeConnections(net.switches)
    print( "Dumping net connections" )
    dumpNetConnections(net)

def simple_tests(net: Mininet):
    print( "Testing network connectivity" )
    net.pingAll()
    print( "Testing bandwidth between hosts" )
    unique_host_tuples_set = set(combinations(net.hosts, 2))
    for host_tuple in unique_host_tuples_set:
        net.iperf(hosts=host_tuple,l4Type='TCP')
        net.iperf(hosts=host_tuple,l4Type='UDP')

def add_default_route(net: Mininet, host: str):
    net[host].cmd('route add default gw 10.0.0.0 {}-eth0'.format(host))

if __name__ == '__main__':
    setLogLevel('info')
    host_count = 0
    if len(sys.argv) != 2:
        print("Usage: {} <host_count>".format(sys.argv[0]))
        print("Usage example: {} 3".format(sys.argv[0]))
        exit(1)
    host_count: int = int(sys.argv[1])
    if host_count < 2:
        print("Please provide a host count greater 1")
        exit(1)
    topo: simple_topo = simple_topo(n = host_count)
    net: Mininet = Mininet(topo=topo, controller=None, link=TCLink)
    net.start()
    for switch in net.switches:
        make_switch_traditional(net, switch.__str__())
        # dump_switch_flows(net, switch.__str__())
        # dump_switch_information(net, switch.__str__())
    # dump_infos(net)
    # simple_tests(net)
    for host in net.hosts:
        add_default_route(net, host.__str__())
    CLI(net)
    net.stop()
else:
    # Command to start CLI w/ topo only: sudo -E mn --mac --controller none --custom ~/vscode-workspaces/topo-1sw-Nhosts.py --topo simple_topo
    topos = {'simple_topo': (lambda: simple_topo())}

# h1 env VSOMEIP_CONFIGURATION=/home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip-configs/vsomeip-udp-service-mininet.json VSOMEIP_APPLICATION_NAME=service-sample /home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip/build/examples/notify-sample &
# h2 env VSOMEIP_CONFIGURATION=/home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip-configs/vsomeip-udp-client-mininet.json VSOMEIP_APPLICATION_NAME=client-sample /home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip/build/examples/subscribe-sample &
