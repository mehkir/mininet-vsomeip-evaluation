#!/usr/bin/bash
RUNTIMESLOG="runtimes.log"
UPPER_BOUND_HOSTS=201
touch $RUNTIMESLOG
RUNS=10
for option in {G..H}; do
    for ((host_count = 2; host_count <= UPPER_BOUND_HOSTS; host_count++)); do
        $(which time) -a -o $RUNTIMESLOG -f "${option}-${host_count}-${RUNS}:\t%E real,\t%U user,\t%S sys"  /home/mehmet/vscode-workspaces/mininet-vsomeip/.venv/bin/python topo-1sw-Nhosts.py --hosts $host_count --evaluate $option --runs $RUNS
    done
done
