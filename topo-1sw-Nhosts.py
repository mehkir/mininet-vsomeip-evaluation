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

def add_default_route(net: Mininet, host_name: str):
    net[host_name].cmd('route add default gw 10.0.0.0 {}-eth0'.format(host_name))

def start_dns_server(net: Mininet, dns_host_name: str):
    dns_host = net[dns_host_name]
    dns_host.cmd("sed -i -E 's/.* # mininet-host-ip/    ip-address: {} # mininet-host-ip/' /home/mehmet/vscode-workspaces/mininet-vsomeip/nsd/nsd.conf".format(dns_host.IP(intf=dns_host.defaultIntf())))
    dns_host.cmd("sed -i -E 's/ns\.service\.         IN    A    .*/ns.service.         IN    A    {}/' /home/mehmet/vscode-workspaces/mininet-vsomeip/zones/service.zone".format(dns_host.IP(intf=dns_host.defaultIntf())))
    dns_host.cmd('nsd-control-setup')
    dns_host.cmd('nsd -c /home/mehmet/vscode-workspaces/mininet-vsomeip/nsd/nsd.conf')

def stop_dns_server(net: Mininet, dns_host_name: str):
    dns_host = net[dns_host_name]
    dns_host.cmd('nsd-control stop')

def create_subscriber_configs(host, dns_host_name: str):
    host_name = host.__str__()
    if host_name != 'h1' and host_name != dns_host_name:
        subscriber_config_template = "/home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip-configs/vsomeip-udp-mininet-subscriber.json"
        host_config = f"/home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip-configs/{host_name}.json"
        host.cmd(f'cp {subscriber_config_template} {host_config}')
        create_host_config(host, host_config)
            # cert path
            # private key path

def create_publisher_config(net: Mininet):
    host = net['h1']
    host_name = host.__str__()
    publisher_config_template = "/home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip-configs/vsomeip-udp-mininet-publisher.json"
    host_config = f"/home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip-configs/{host_name}.json"
    host.cmd(f'cp {publisher_config_template} {host_config}')
    create_host_config(host, host_config)
    # cert path
    # private key path

def create_host_config(host, host_config: str):
    host_name = host.__str__()
    unicast_ip = host.IP(intf=host.defaultIntf())
    host.cmd(f"sed -i -E 's/    \"network\" : .*,/    \"network\" : \"-{host_name}\",/' {host_config}")
    host.cmd(f"sed -i -E 's/    \"unicast\" : .*,/    \"unicast\" : \"{unicast_ip}\",/' {host_config}")
    host.cmd(f"sed -i -E 's/        \"file\" : .*,/        \"file\" : {{ \"enable\" : \"false\", \"path\" : \"\/var\/log\/{host_name}.log\" }},/' {host_config}")
    host.cmd(f"sed -i -E 's/            \"name\" : .*,/            \"name\" : \"{host_name}\",/' {host_config}")
    host_id = "0x{:04x}".format(int(host.__str__()[1:]))
    host.cmd(f"sed -i -E 's/            \"id\" : .*/            \"id\" : \"{host_id}\"/' {host_config}")
    host.cmd(f"sed -i -E 's/    \"routing\" : .*,/    \"routing\" : \"{host_name}\",/' {host_config}")

def build_vsomeip():
    subprocess.run("/home/mehmet/vscode-workspaces/mininet-vsomeip/build_vsomeip.bash")

if __name__ == '__main__':
    setLogLevel('info')
    maximum_possible_hosts: int = 0xffff
    host_count: int = 0
    if len(sys.argv) != 2:
        print("Usage: {} <host_count>".format(sys.argv[0]))
        print("Usage example: {} 3".format(sys.argv[0]))
        exit(1)
    host_count: int = int(sys.argv[1])
    if host_count < 2:
        print("Please provide a host count greater 1")
        exit(1)
    if host_count > maximum_possible_hosts:
        print("Please provide a host count less or equal {}".format(maximum_possible_hosts))
        exit(1)
    build_vsomeip()
    topo: simple_topo = simple_topo(n = host_count+1)
    net: Mininet = Mininet(topo=topo, controller=None, link=TCLink)
    net.start()
    for switch in net.switches:
        make_switch_traditional(net, switch.__str__())
        # dump_switch_flows(net, switch.__str__())
        # dump_switch_information(net, switch.__str__())
    # dump_infos(net)
    # simple_tests(net)
    dns_host_name: str = "h{}".format(host_count+1)
    start_dns_server(net, dns_host_name)
    create_publisher_config(net)
    for host in net.hosts:
        add_default_route(net, host.__str__())
        create_subscriber_configs(host, dns_host_name)
    CLI(net)
    stop_dns_server(net, dns_host_name)
    # delete host configs
    for host in net.hosts:
        host_name: str = host.__str__()
        if host_name != dns_host_name:
            host_config: str = f"/home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip-configs/{host_name}.json"
            host.cmd(f'rm {host_config}')
    net.stop()
else:
    # Command to start CLI w/ topo only: sudo -E mn --mac --controller none --custom ~/vscode-workspaces/topo-1sw-Nhosts.py --topo simple_topo
    topos = {'simple_topo': (lambda: simple_topo())}

# branch: working master
# h1 env VSOMEIP_CONFIGURATION=/home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip-configs/vsomeip-udp-service-mininet.json VSOMEIP_APPLICATION_NAME=service-sample /home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip/build/examples/notify-sample &
# h2 env VSOMEIP_CONFIGURATION=/home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip-configs/vsomeip-udp-client-mininet.json VSOMEIP_APPLICATION_NAME=client-sample /home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip/build/examples/subscribe-sample &

# branch: multiple_services/dns_and_dane
# h1 env VSOMEIP_CONFIGURATION=/home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip-configs/vsomeip-udp-mininet-publisher.json VSOMEIP_APPLICATION_NAME=mininet-publisher /home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip/build/examples/mininet-publisher &
# h2 env VSOMEIP_CONFIGURATION=/home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip-configs/vsomeip-udp-mininet-subscriber.json VSOMEIP_APPLICATION_NAME=mininet-subscriber /home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip/build/examples/mininet-subscriber &