# from java:

# PV name prefix:                   "IOC:BSY0:MP01"
# pv event IOC:                     "EVNT:SYS0:1:LCLS"
# pv heartbit:                      "MPS:SYS0:1:GUI_HRTBT" 

# TEST THE FULL GUI APPLICATION RUN BY PDYM:
# Currently adjusted to a testing configuration in MpsConfiguration-R2-207

# pydm --hide-nav-bar --hide-status-bar --hide-menu-bar \
#     -m "configDB_Prefix=${EPICS_IOC_TOP}/MpsConfiguration/MpsConfiguration-R2-207/database, \
#     logicDB_Prefix=${EPICS_IOC_TOP}/MpsConfiguration/MpsConfiguration-R2-207/algorithm, \
#     IOC_PREFIX=IOC:BSY0:MP01, \
#     JSONFILEPATH=recent_states.json, \
#     accel_type = LCLS" \
#     mps_gui_main.py



# DONT UUUUUUUUUSEE THIS FOR THE FINAL VERSION
# AHHHHHHHH
# THIS IS TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY
# I had to create a temporary workaround due to a discreptency between dev and lcls 
pydm --hide-nav-bar --hide-status-bar --hide-menu-bar \
    -m "configDB_Prefix='', \
    logicDB_Prefix='', \
    IOC_PREFIX=IOC:BSY0:MP01, \
    JSONFILEPATH=recent_states_lcls.json, \
    accel_type = LCLS" \
    mps_gui_main.py