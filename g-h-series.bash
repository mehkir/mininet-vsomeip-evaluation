#!/usr/bin/bash

for option in {G..H}; do
    for host_count in {2..201}; do
         echo "OPTION $option WITH $host_count hosts"
        /home/mehmet/vscode-workspaces/mininet-vsomeip/.venv/bin/python topo-1sw-Nhosts.py --hosts $host_count --evaluate $option --runs 50
    done
done
