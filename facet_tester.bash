# ./jar/mpsgui.jar 
# "client" 
# "yesHistory" 
# "FACET" 
# "IOC:SYS1:MP01" 
# "EVNT:SYS1:1:"
#  "null" 
#  "/u1/facet/physics/mpsgui_recentFaults/recentFaults_file.json" 
#  jdbc:sqlite:${EPICS_IOC_TOP}/MpsConfiguration-FACET/current/database/ 
#  jdbc:sqlite:${EPICS_IOC_TOP}/MpsConfiguration-FACET/current/algorithm/ ${HIST_JDBC_URL} \


# TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY
#  TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY
# TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY
#  TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY
 pydm --hide-nav-bar --hide-status-bar --hide-menu-bar \
    -m "configDB_Prefix=${EPICS_IOC_TOP}/MpsConfiguration-FACET/MpsConfiguration-FACET-R1-17/database/, \
    logicDB_Prefix=${EPICS_IOC_TOP}/MpsConfiguration-FACET/MpsConfiguration-FACET-R1-17/algorithm/, \
    IOC_PREFIX=IOC:SYS1:MP01, \
    JSONFILEPATH=recent_states_facet.json,\
    accel_type = FACET" \
    mps_gui_main.py