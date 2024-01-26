#!/usr/bin/python

"""Custom topology

N hosts directly connected to one switch

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

import argparse
import subprocess
from itertools import combinations
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.util import dumpNodeConnections
from mininet.util import dumpNetConnections

PUBLISHER_HOST_NAME = 'h1'
PROJECT_PATH = "/home/mehmet/vscode-workspaces/mininet-vsomeip"

SERVICE_ID = "4660"
INSTANCE_ID = "22136"
MAJOR_VERSION = "0"
MINOR_VERSION = "0"
PUBLISHER_PORT = "30509"
SUBSCRIBER_PORTS = "40000,40002"
PROTOCOL = "UDP"
# compile definitions
WITH_SERVICE_AUTHENTICATION = 'WITH_SERVICE_AUTHENTICATION'
WITH_CLIENT_AUTHENTICATION = 'WITH_CLIENT_AUTHENTICATION'
WITH_ENCRYPTION = 'WITH_ENCRYPTION'
WITH_SOMEIP_SD = 'WITH_SOMEIP_SD'
WITH_DANE = 'WITH_DANE'
# branches
VANILLA = 'multiple_services/vanilla'
DNS_AND_DANE = 'multiple_services/dns_and_dane'

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

def add_default_route(host):
    host_name = host.__str__()
    host.cmd(f'route add default gw 10.0.0.0 {host_name}-eth0')

def set_dns_server_ip_in_vsomeip(dns_host):
    dns_host_ip = dns_host.IP(intf=dns_host.defaultIntf())
    ip_bytes = dns_host_ip.split(".")
    ip_bytes_in_hex = [ "{:02x}".format(int(x)) for x in ip_bytes ]
    dns_host_ip_in_hex = f"0x{''.join(ip_bytes_in_hex)}"
    result = dns_host.cmd(f"grep \"#define DNS_SERVER_IP\" {PROJECT_PATH}/vsomeip/implementation/dnssec/include/someip_dns_parameters.hpp | awk '{{print $3}}'")
    current_dns_server_ip = result.strip()
    if current_dns_server_ip != dns_host_ip_in_hex:
        dns_host.cmd(f"sed -i -E 's/#define DNS_SERVER_IP .*/#define DNS_SERVER_IP {dns_host_ip_in_hex}/' {PROJECT_PATH}/vsomeip/implementation/dnssec/include/someip_dns_parameters.hpp")

def set_subscriber_count_to_record_in_vsomeip(subscriber_count_to_record: int):
    result = subprocess.run(f"grep \"#define SUBSCRIBER_COUNT_TO_RECORD\" {PROJECT_PATH}/vsomeip/implementation/service_discovery/src/service_discovery_impl.cpp | awk '{{print $3}}'", shell=True, stdout=subprocess.PIPE, text=True)
    current_subscriber_count = int(result.stdout.strip())
    if current_subscriber_count != subscriber_count_to_record:
        subprocess.run(f"sed -i -E 's/#define SUBSCRIBER_COUNT_TO_RECORD .*/#define SUBSCRIBER_COUNT_TO_RECORD {subscriber_count_to_record}/' {PROJECT_PATH}/vsomeip/implementation/service_discovery/src/service_discovery_impl.cpp", shell=True)

def start_dns_server(dns_host):
    dns_host_ip = dns_host.IP(intf=dns_host.defaultIntf())
    dns_host.cmd(f"sed -i -E 's/.* # mininet-host-ip/    ip-address: {dns_host_ip} # mininet-host-ip/' {PROJECT_PATH}/nsd/nsd.conf")
    dns_host.cmd(f"sed -i -E 's/ns\.service\.         IN    A    .*/ns.service.         IN    A    {dns_host_ip}/' {PROJECT_PATH}/zones/service.zone")
    dns_host.cmd(f"sed -i -E 's/ns\.client\.         IN    A    .*/ns.client.         IN    A    {dns_host_ip}/' {PROJECT_PATH}/zones/client.zone")
    dns_host.cmd('nsd-control-setup')
    dns_host.cmd(f'nsd -c {PROJECT_PATH}/nsd/nsd.conf')

def stop_dns_server(dns_host):
    dns_host.cmd('nsd-control stop')
    dns_host.cmd('pkill nsd')

def create_subscriber_config(host):
    host_name = host.__str__()
    subscriber_config_template = f"{PROJECT_PATH}/vsomeip-configs/vsomeip-udp-mininet-subscriber.json"
    host_config = f"{PROJECT_PATH}/vsomeip-configs/{host_name}.json"
    host.cmd(f'cp {subscriber_config_template} {host_config}')
    create_host_config(host, host_config)

def create_publisher_config(host):
    host_name = host.__str__()
    publisher_config_template = f"{PROJECT_PATH}/vsomeip-configs/vsomeip-udp-mininet-publisher.json"
    host_config = f"{PROJECT_PATH}/vsomeip-configs/{host_name}.json"
    host.cmd(f'cp {publisher_config_template} {host_config}')
    create_host_config(host, host_config)

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

def create_client_certificate(host):
    host_name = host.__str__()
    host_id = str(host_name[1:])
    host_ip = host.IP(intf=host.defaultIntf())
    host_config = f"{PROJECT_PATH}/vsomeip-configs/{host_name}.json"
    host.cmd(f'{PROJECT_PATH}/client-svcb-and-tlsa-generator.bash {host_id} {SERVICE_ID} {INSTANCE_ID} {MAJOR_VERSION} {host_ip} {SUBSCRIBER_PORTS} {PROTOCOL} {host_name}')
    certificate_path = f"\/home\/mehmet\/vscode-workspaces\/mininet-vsomeip\/certificates\/{host_name}.client.cert.pem"
    private_key_path = f"\/home\/mehmet\/vscode-workspaces\/mininet-vsomeip\/certificates\/{host_name}.client.key.pem"
    host.cmd(f"sed -i -E 's/    \"certificate-path\" : .*,/    \"certificate-path\" : \"{certificate_path}\",/' {host_config}")
    host.cmd(f"sed -i -E 's/    \"private-key-path\" : .*/    \"private-key-path\" : \"{private_key_path}\"/' {host_config}")

def create_service_certificate(host):
    host_name = host.__str__()
    host_ip = host.IP(intf=host.defaultIntf())
    host_config = f"{PROJECT_PATH}/vsomeip-configs/{host_name}.json"
    host.cmd(f'{PROJECT_PATH}/service-svcb-and-tlsa-generator.bash {SERVICE_ID} {INSTANCE_ID} {MAJOR_VERSION} {MINOR_VERSION} {host_ip} {PUBLISHER_PORT} {PROTOCOL} {host_name}')
    certificate_path = f"\/home\/mehmet\/vscode-workspaces\/mininet-vsomeip\/certificates\/{host_name}.service.cert.pem"
    private_key_path = f"\/home\/mehmet\/vscode-workspaces\/mininet-vsomeip\/certificates\/{host_name}.service.key.pem"
    host.cmd(f"sed -i -E 's/    \"certificate-path\" : .*,/    \"certificate-path\" : \"{certificate_path}\",/' {host_config}")
    host.cmd(f"sed -i -E 's/    \"private-key-path\" : .*/    \"private-key-path\" : \"{private_key_path}\"/' {host_config}")

def reset_zone_files():
    subprocess.run(["su", "-", "mehmet", "-c", f"{PROJECT_PATH}/reset-zone-file.bash"])

def start_someip_subscriber_app(host):
    host_name = host.__str__()
    host.cmd(f"env VSOMEIP_CONFIGURATION={PROJECT_PATH}/vsomeip-configs/{host_name}.json  VSOMEIP_APPLICATION_NAME={host_name} {PROJECT_PATH}/vsomeip/build/examples/my-subscriber &")

def start_someip_publisher_app(host):
    host_name = host.__str__()
    host.cmd(f"env VSOMEIP_CONFIGURATION={PROJECT_PATH}/vsomeip-configs/{host_name}.json  VSOMEIP_APPLICATION_NAME={host_name} {PROJECT_PATH}/vsomeip/build/examples/my-publisher &")

def stop_subscriber_app(host):
    host.cmd("pkill my-subscriber")

def stop_publisher_app(host):
    host.cmd("pkill my-publisher")

def switch_someip_branch(branch_name: str):
    result = subprocess.run(f"cd {PROJECT_PATH}/vsomeip && git checkout {branch_name}", shell=True)
    return result.returncode

def build_vsomeip():
    subprocess.run(["su", "-", "mehmet", "-c", f"{PROJECT_PATH}/build_vsomeip.bash"])

if __name__ == '__main__':
    setLogLevel('info')
    maximum_possible_hosts: int = 0xffff
    parser = argparse.ArgumentParser(description='Starts vsomeip w/ or w/o security mechanisms and collects timestamps of handshake events')
    parser.add_argument('--hosts', type=int, metavar='N', required=True, choices=range(2,0xffff+1), help='Specify the number of hosts. (between 2 (inclusive) and 65536 (exclusive))')
    parser.add_argument('--evaluate', choices=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'], required=True, help="""A: vanilla (vsomeip as it is),
                                                                                                                        B: w/ service authentication,
                                                                                                                        C: w/ service and client authentication,
                                                                                                                        D: w/ service and client authentication + payload encryption,
                                                                                                                        E: w/ DNSSEC w/o SOME/IP SD,
                                                                                                                        F: w/ DNSSEC + SOME/IP SD,
                                                                                                                        G: w/ DNSSEC + DANE w/o SOME/IP SD,
                                                                                                                        H: w/ DNSSEC + DANE + SOME/IP SD,
                                                                                                                        I: w/ DNSSEC + DANE + SOME/IP SD + client authentication,
                                                                                                                        J: w/ DNSSEC + DANE + SOME/IP SD + client authentication + payload encryption""")
    args = parser.parse_args()
    host_count: int = args.hosts
    evaluation_option: str = args.evaluate
    compile_definitions = {'A':'',
                           'B':f'{WITH_SERVICE_AUTHENTICATION}',
                           'C':f'{WITH_SERVICE_AUTHENTICATION} {WITH_CLIENT_AUTHENTICATION}',
                           'D':f'{WITH_SERVICE_AUTHENTICATION} {WITH_CLIENT_AUTHENTICATION} {WITH_ENCRYPTION}',
                           'E':'',
                           'F':f'{WITH_SOMEIP_SD}',
                           'G':f'{WITH_DANE}',
                           'H':f'{WITH_DANE} {WITH_SOMEIP_SD}',
                           'I':f'{WITH_DANE} {WITH_SOMEIP_SD} {WITH_CLIENT_AUTHENTICATION}',
                           'J':f'{WITH_DANE} {WITH_SOMEIP_SD} {WITH_CLIENT_AUTHENTICATION} {WITH_ENCRYPTION}'}
    branches = {'A':VANILLA,
                'B':VANILLA,
                'C':VANILLA,
                'D':VANILLA,
                'E':DNS_AND_DANE,
                'F':DNS_AND_DANE,
                'G':DNS_AND_DANE,
                'H':DNS_AND_DANE,
                'I':DNS_AND_DANE,
                'J':DNS_AND_DANE,}
    switch_branch = branches[evaluation_option]
    add_compile_definitions = compile_definitions[evaluation_option]
    if switch_someip_branch(switch_branch):
        print("Couldn't switch branch. Check git repository state.")
        exit(1)
    # setup vsomeip
    set_subscriber_count_to_record_in_vsomeip(host_count-1)
    build_vsomeip()
    # start statistics writer
    statistics_writer_process = subprocess.Popen([f"{PROJECT_PATH}/vsomeip/build/implementation/statistics/statistics-writer-main", str(host_count-1), f"{PROJECT_PATH}/statistic-results"])
    # build mininet network
    topo: simple_topo = simple_topo(n = host_count+1)
    net: Mininet = Mininet(topo=topo, controller=None, link=TCLink)
    net.start()
    for switch in net.switches:
        make_switch_traditional(net, switch.__str__())
    # setup dns server
    reset_zone_files()
    dns_host_name: str = f"h{host_count+1}"
    set_dns_server_ip_in_vsomeip(net[dns_host_name])
    start_dns_server(net[dns_host_name])
    # create host configs and certificates
    create_publisher_config(net[PUBLISHER_HOST_NAME])
    create_service_certificate(net[PUBLISHER_HOST_NAME])
    for host in net.hosts:
        add_default_route(host)
        host_name = host.__str__()
        if host_name != PUBLISHER_HOST_NAME and host_name != dns_host_name:
            create_subscriber_config(host)
            create_client_certificate(host)
    # start someip publisher and subscribers
    start_someip_publisher_app(net[PUBLISHER_HOST_NAME])
    for host in net.hosts:
        host_name = host.__str__()
        if host_name != PUBLISHER_HOST_NAME and host_name != dns_host_name:
            start_someip_subscriber_app(host)
    # Wait for statistics writer
    return_code = statistics_writer_process.wait()
    if return_code == 0:
        print("statistics writer executed successfully")
    else:
        print(f"statistics writer failed with return code {return_code}")
    CLI(net)
    # stop someip publisher, subscribers and dns server
    for host in net.hosts:
        host_name: str = host.__str__()
        if host_name != dns_host_name:
            if host_name != PUBLISHER_HOST_NAME:
                stop_subscriber_app(host)
            else:
                stop_publisher_app(host)
    stop_dns_server(net[dns_host_name])
    net.stop()
    #cleanup
    reset_zone_files()
    subprocess.run(["pkill", "statistics-writ"])
    subprocess.run(f"rm -f {PROJECT_PATH}/vsomeip-h*", shell=True)
    subprocess.run("rm -f /var/log/h*.log", shell=True)
    subprocess.run(f"rm -f {PROJECT_PATH}/vsomeip-configs/h*.json", shell=True)
    subprocess.run(f"rm -f {PROJECT_PATH}/certificates/*", shell=True)
else:
    # Command to start CLI w/ topo only: sudo -E mn --mac --controller none --custom ~/vscode-workspaces/topo-1sw-Nhosts.py --topo simple_topo
    topos = {'simple_topo': (lambda: simple_topo())}
