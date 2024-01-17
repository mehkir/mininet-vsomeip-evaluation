#!/usr/bin/bash

cmake -B /home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip/build -S /home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip
$(which cmake) --build /home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip/build --config Release --target all -- -j$(nproc)
$(which cmake) --build /home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip/build --config Release --target examples -- -j$(nproc)
$(which cmake) --build /home/mehmet/vscode-workspaces/mininet-vsomeip/vsomeip/build --config Release --target statistics-writer -- -j$(nproc)