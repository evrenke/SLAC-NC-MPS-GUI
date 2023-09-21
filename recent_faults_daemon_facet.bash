#!/bin/bash

# MONITOR THE CURRENT STATES, AND LOG CHANGES INTO A GIVEN JSON:

# CONFIG_DB_FILE=${EPICS_IOC_TOP}/MpsConfiguration-FACET/current/database/
# LOGIC_DB_FILE=${EPICS_IOC_TOP}/MpsConfiguration-FACET/current/algorithm/
# IOC_PREFIX=IOC:SYS1:MP01
# RECENT_FAULTS_DB=dbinteraction/recentStatesDB/recent_states_facet.sqlite
# ACCEL_TYPE=FACET

cd "$(dirname "${BASH_SOURCE[0]}")"

python recent_faults_daemon.py ${EPICS_IOC_TOP}/MpsConfiguration-FACET/current/database/ \
    ${EPICS_IOC_TOP}/MpsConfiguration-FACET/current/algorithm/ \
    IOC:SYS1:MP01 \
    dbinteraction/recentStatesDB/recent_states_facet.sqlite \
    FACET