#!/usr/bin/bash
RUNTIMESLOG="runtimes.log"
touch $RUNTIMESLOG
RUNS=1
for option in {G..H}; do
    for host_count in {2..3}; do
        $(which time) -a -o $RUNTIMESLOG -f "${option}-${host_count}-${RUNS}:\t%E real,\t%U user,\t%S sys"  /home/mehmet/vscode-workspaces/mininet-vsomeip/.venv/bin/python topo-1sw-Nhosts.py --hosts $host_count --evaluate $option --runs $RUNS
    done
done
