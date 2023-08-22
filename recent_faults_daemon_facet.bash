# MONITOR THE CURRENT STATES, AND LOG CHANGES INTO A GIVEN JSON:

# accel_type=FACET
# IOC_PREFIX=IOC:SYS1:MP01
# CONFIG_DB_FILE=${EPICS_IOC_TOP}/MpsConfiguration-FACET/current/database/
# LOGIC_DB_FILE=${EPICS_IOC_TOP}/MpsConfiguration-FACET/current/algorithm/
# JSONFILEPATH=recent_states_facet.json;;

# python recent_faults_daemon.py ${EPICS_IOC_TOP}/MpsConfiguration-FACET/MpsConfiguration-FACET-R1-17/database/ \
#     ${EPICS_IOC_TOP}/MpsConfiguration-FACET/MpsConfiguration-FACET-R1-17/algorithm/ \
#     IOC:SYS1:MP01 \
#     recent_states_facet.json \
#     FACET

python recent_faults_daemon.py ${EPICS_IOC_TOP}/MpsConfiguration-FACET/current/database/ \
    ${EPICS_IOC_TOP}/MpsConfiguration-FACET/current/algorithm/ \
    IOC:SYS1:MP01 \
    recent_states_facet.json \
    FACET