# MONITOR THE CURRENT STATES, AND LOG CHANGES INTO A GIVEN JSON:

# python recent_faults_daemon.py ${EPICS_IOC_TOP}/MpsConfiguration/MpsConfiguration-R2-207/database \
#     ${EPICS_IOC_TOP}/MpsConfiguration/MpsConfiguration-R2-207/algorithm \
#     IOC:BSY0:MP01 \
#     recent_states.json

python recent_faults_daemon.py '' \
    '' \
    IOC:BSY0:MP01 \
    recent_states_lcls.json \
    LCLS