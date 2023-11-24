#!/usr/bin/bash
mkdir -p nsd
wget https://nlnetlabs.nl/downloads/nsd/nsd-4.7.0.tar.gz
tar xzf nsd-4.7.0.tar.gz
cd nsd-4.7.0
./configure --with-configdir=/home/mehmet/vscode-workspaces/mininet-vsomeip/nsd --with-nsd_conf_file=/home/mehmet/vscode-workspaces/mininet-vsomeip/nsd/nsd.conf
make -j$(nproc)
printf "\n\tExeute 'sudo make -j$(nproc) install' in nsd-4.7.0 directory and then 'nsd-control-setup'\n"