# MONITOR THE CURRENT STATES, AND LOG CHANGES INTO A GIVEN JSON:

# python recent_faults_daemon.py ${EPICS_IOC_TOP}/MpsConfiguration/MpsConfiguration-R2-207/database \
#     ${EPICS_IOC_TOP}/MpsConfiguration/MpsConfiguration-R2-207/algorithm \
#     IOC:BSY0:MP01 \
#     recent_states.json

python recent_faults_daemon.py ${EPICS_IOC_TOP}/MpsConfiguration-FACET/MpsConfiguration-FACET-R1-17/database/ \
    ${EPICS_IOC_TOP}/MpsConfiguration-FACET/MpsConfiguration-FACET-R1-17/algorithm/ \
    IOC:SYS1:MP01 \
    recent_states_facet.json \
    FACET