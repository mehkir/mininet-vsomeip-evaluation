#!/usr/bin/bash

OPTION=H
STATISTICS_PATH=./statistic-results/${OPTION}-series
EXPECTED_SAMPLES_COUNT=50
UPPER_BOUND_HOST_COUNT=150
for ((host_count = 2; host_count <= UPPER_BOUND_HOST_COUNT; host_count++)); do
    current_samples_count=$(ls ${STATISTICS_PATH}/${OPTION}-${host_count}-* | wc -l)
    if [[ $current_samples_count != $EXPECTED_SAMPLES_COUNT ]]; then
        echo "${OPTION}-${host_count} has ${current_samples_count} samples"
    fi
done
