#!/bin/bash

# MONITOR THE CURRENT STATES, AND LOG CHANGES INTO A GIVEN JSON:

# CONFIG_DB_FILE=${EPICS_IOC_TOP}/MpsConfiguration/current/database/
# LOGIC_DB_FILE=${EPICS_IOC_TOP}/MpsConfiguration/current/algorithm/
# IOC_PREFIX='IOC:BSY0:MP01'
# RECENT_FAULTS_DB=dbinteraction/recentStatesDB/recent_states_lcls.sqlite
# ACCEL_TYPE='LCLS'

cd "$(dirname "${BASH_SOURCE[0]}")"

python recent_faults_daemon.py ${EPICS_IOC_TOP}/MpsConfiguration/current/database \
    ${EPICS_IOC_TOP}/MpsConfiguration/current/algorithm \
    IOC:BSY0:MP01 \
    dbinteraction/recentStatesDB/recent_states_lcls.sqlite \
    LCLS