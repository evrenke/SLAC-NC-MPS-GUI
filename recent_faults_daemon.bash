# MONITOR THE CURRENT STATES, AND LOG CHANGES INTO A GIVEN JSON:

# accel_type='LCLS'
# IOC_PREFIX='IOC:BSY0:MP01'
# CONFIG_DB_FILE=${EPICS_IOC_TOP}/MpsConfiguration/current/database/
# LOGIC_DB_FILE=${EPICS_IOC_TOP}/MpsConfiguration/current/algorithm/
# JSONFILEPATH=recent_states_lcls.json

python recent_faults_daemon.py ${EPICS_IOC_TOP}/MpsConfiguration/current/database \
    ${EPICS_IOC_TOP}/MpsConfiguration/current/algorithm \
    IOC:BSY0:MP01 \
    recent_states_lcls.json \
    LCLS