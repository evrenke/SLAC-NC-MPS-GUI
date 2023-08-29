# Flexible bash script that can launch the 6 different possible configurations of the mps gui
# LCLS main mode, summary cud mode or recent faults cud mode
# FACET main mode, summary cud mode or recent faults cud mode

# It can also take in additional parameters like database file paths to override the default file paths

# cd "$(dirname "${BASH_SOURCE[0]}")"

usage(){
    echo "LCLS-NC/FACET MPS GUI launcher"
    echo "Usage:" 1>&2
    echo "  nc_mps_gui.bash [-f | --facet] [ -c | --cud TYPE ] [ -confd | --configdbfile CONFIG_DB_FILE ] [ -logicd | --logicdbfile LOGIC_DB_FILE ]" 1>&2
    echo "" 1>&2
    echo "Examples:" 1>&2
    echo "  nc_mps_gui.bash" 1>&2
    echo "  nc_mps_gui.bash -f" 1>&2
    echo "  nc_mps_gui.bash  --configdbfile ~/database/my_file.db --logicdbfile ~/algorithm/my_other_file.db" 1>&2
    echo "For the MPS CUD use:" 1>&2
    echo "  nc_mps_gui.bash  --cud summary" 1>&2
    echo "  nc_mps_gui.bash  -f --cud recent" 1>&2
    echo "  nc_mps_gui.bash -c summary" 1>&2
}
exit_abnormal(){
    usage
    exit 1
}

# default to LCLS
accel_type='LCLS'
CUD_MODE=''
IOC_PREFIX='IOC:BSY0:MP01'
CONFIG_DB_FILE=${EPICS_IOC_TOP}/MpsConfiguration/current/database/
LOGIC_DB_FILE=${EPICS_IOC_TOP}/MpsConfiguration/current/algorithm/
JSONFILEPATH=recent_states_lcls.json


while [ $# -gt 0 ]
do
    echo $1
    case $1 in
        -f | --facet) accel_type=FACET
        IOC_PREFIX=IOC:SYS1:MP01
        CONFIG_DB_FILE=${EPICS_IOC_TOP}/MpsConfiguration-FACET/current/database/
        LOGIC_DB_FILE=${EPICS_IOC_TOP}/MpsConfiguration-FACET/current/algorithm/
        JSONFILEPATH=recent_states_facet.json;;
        -c | --cud) CUD_MODE="$2" 
                    shift 
                    echo $CUD_MODE;;
        -confd | --configdbfile) CONFIG_DB_FILE="$2" 
                                 shift;;
        -logicd | --logicdbfile) LOGIC_DB_FILE="$2"
                                 shift;;
        -h | --help) exit_abnormal ;;
        *) exit_abnormal
    esac
    shift
done

# not working lol
if [$CUD_MODE == 'recent']
then
    $CUD_MODE = 'recent'
fi 

if [$CUD_MODE == 'summary']
then
    $CUD_MODE = 'summary'
fi 

MACROS="accel_type=$accel_type, IOC_PREFIX=$IOC_PREFIX, configDB_Prefix=$CONFIG_DB_FILE, logicDB_Prefix=$LOGIC_DB_FILE, JSONFILEPATH=$JSONFILEPATH"



if [[ -n $CUD_MODE ]]
then
    MACROS+=", CUD=$CUD_MODE"
fi
echo $MACROS

pydm --hide-nav-bar --hide-status-bar --hide-menu-bar \
    -m "$MACROS" \
    mps_gui_main.py

exit 0


# Example commands:
# LCLS running for 3 modes. main, summary cud, and recent faults cud
# sh nc_mps_gui.bash 

# sh nc_mps_gui.bash -c summary 

# sh nc_mps_gui.bash -c recent


# FACET running on dev for 3 modes. main, summary cud, and recent faults cud:
# sh nc_mps_gui.bash -f -confd ${EPICS_IOC_TOP}/MpsConfiguration-FACET/MpsConfiguration-FACET-R1-17/database/ -logicd ${EPICS_IOC_TOP}/MpsConfiguration-FACET/MpsConfiguration-FACET-R1-17/algorithm/

# sh nc_mps_gui.bash -f -c summary -confd ${EPICS_IOC_TOP}/MpsConfiguration-FACET/MpsConfiguration-FACET-R1-17/database/ -logicd ${EPICS_IOC_TOP}/MpsConfiguration-FACET/MpsConfiguration-FACET-R1-17/algorithm/

# sh nc_mps_gui.bash -f -c recent -confd ${EPICS_IOC_TOP}/MpsConfiguration-FACET/MpsConfiguration-FACET-R1-17/database/ -logicd ${EPICS_IOC_TOP}/MpsConfiguration-FACET/MpsConfiguration-FACET-R1-17/algorithm/
