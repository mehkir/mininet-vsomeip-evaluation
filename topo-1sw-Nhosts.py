#!/usr/bin/python

"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

import sys
import time
import subprocess
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.util import dumpNodeConnections
from mininet.util import dumpNetConnections

ABSOLUTE_PROJECT_PATH="/home/mehmet/vscode-workspaces/mininet-dh-key-agreement/dh-key-agreement"
ABSOLUTE_RESULTS_DIRECTORY_PATH=ABSOLUTE_PROJECT_PATH+"/statistic_results/test_runs_without_retransmissions"
SERVICE_ID=42
SCATTER_DELAY_MIN=0
SCATTER_DELAY_MAX=0
MULTICAST_IP="239.255.0.1"
MULTICAST_PORT=65000

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
    print( "Testing bandwidth between h1 and h2" )
    h1, h2 = net['h1'], net['h2']
    net.iperf(hosts=(h1, h2),l4Type='TCP')
    net.iperf(hosts=(h1, h2),l4Type='UDP')

def get_members_up_count_by_unique_ports() -> int:
    result = subprocess.run(args="ss -lup | grep multicast-dh-ex | awk '{print $4}' |  awk -F: '{print $NF}' | grep -v " + str(MULTICAST_PORT) + " | sort -u | wc -l", shell=True, capture_output=True, text=True)
    return int(result.stdout.strip())

def get_process_count() -> int:
    result = subprocess.run(args="pgrep multicast-dh | wc -l", shell=True, capture_output=True, text=True)
    return int(result.stdout.strip())

def start_subscribers_and_publisher(net: Mininet):
    host_count = len(net.hosts)
    for host in net.hosts:
        if host.__str__() != 'h1':
            listening_interface_by_ip = host.IP(intf=host.defaultIntf())
            host.cmd('{}/build/multicast-dh-example false {} {} {} {} {} {} {} &'.format(ABSOLUTE_PROJECT_PATH, SERVICE_ID, host_count, SCATTER_DELAY_MIN, SCATTER_DELAY_MAX, listening_interface_by_ip, MULTICAST_IP, MULTICAST_PORT))

    # while get_process_count() < host_count-1:
    #     time.sleep(1)

    publisher_host = net['h1']
    subscriber_online_count = int(publisher_host.cmd("pgrep multicast-dh | wc -l").strip())
    while subscriber_online_count < host_count-1:
        subscriber_online_count = int(publisher_host.cmd("pgrep multicast-dh | wc -l").strip())
        print("{} subscribers are up".format(subscriber_online_count))
        time.sleep(1)

    listening_interface_by_ip = publisher_host.IP(intf=publisher_host.defaultIntf())
    publisher_host.cmd('{}/build/multicast-dh-example true {} {} {} {} {} {} {} &'.format(ABSOLUTE_PROJECT_PATH, SERVICE_ID, host_count, SCATTER_DELAY_MIN, SCATTER_DELAY_MAX, listening_interface_by_ip, MULTICAST_IP, MULTICAST_PORT))


if __name__ == '__main__':
    setLogLevel('info')
    host_count: int = int(sys.argv[1])
    topo: simple_topo = simple_topo(n = host_count)
    net: Mininet = Mininet(topo=topo, controller=None, link=TCLink)
    net.start()
    make_switch_traditional(net,'s1')
    # dump_switch_flows(net, 's1')
    # dump_switch_information(net, 's1')
    # dump_infos(net)
    # simple_tests(net)
    statistics_writer_process = subprocess.Popen(args="{}/build/statistics-writer-main {} {}".format(ABSOLUTE_PROJECT_PATH, host_count, ABSOLUTE_RESULTS_DIRECTORY_PATH) ,shell=True)
    start_subscribers_and_publisher(net)
    print("Waiting for statistics writer process to finish")
    statistics_writer_process.wait()
    #CLI(net)
    net.stop()
else:
    # Command to start CLI w/ topo only: sudo -E mn --mac --controller none --custom ~/vscode-workspaces/topo-1sw-2host.py --topo simple_topo
    topos = {'simple_topo': (lambda: simple_topo())}