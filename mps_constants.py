RECENT_FAULTS_MAX = 1000
"""Amount of recent faults to record"""
# Number of secs until 01/01/1990 00:00:00 from
# http://www.onlineconversion.com/unix_time.htm
FROM_1970_TO_1990_IN_SECONDS = 631152000
"""the seconds count from the Epoch (Jan 1st 1970) to an internal date"""

CURRENT_STATES_POSTFIX = ':TTBLST.VALA'
"""Postfix to get an int8 array of current state values"""
BYPASS_VALUE_POSTFIX = '_BYPV.RVAL'
"""Postfix to get what a bypass value of a PV is"""
BYPASS_DURATION_POSTFIX = '_BYPC'
"""Postfix to get seconds of duration from when the bypass started"""
BYPASS_STRING_POSTFIX = '_BYPS'
"""Postfix to get what the string value of a PV bypass is"""
FAULT_STATE_POSTFIX = '_MPS'
"""Postfix to get the value of a PV, 0 or 1"""
FAULT_STATE_CURRENT_POSTFIX = '_MPSC'
"""Postfix to get the unlatched value of a PV, 0 or 1"""
STATE_IS_OK_POSTFIX = '_MPS.RVAL'
"""Postfix to get if the state of a PV is ok"""
CHANNEL_PREFIX = 'ca://'
"""Channel prefix to add behind PV's"""
BYPASS_FAULT_NUMBERS_POSTFIX = ':BYPASS_LIST.VALA'
"""Postfix that gets bypass numbers with IOC prefix"""
BYPASS_SECONDS_POSTFIX = ':BYPASS_LIST.VALB'
"""Postfix that gets the seconds duration of bypasses with IOC prefix"""
CONFIG_VERSION_POSTFIX = ':DBVERS'
"""Postfix that tells us the config version"""
LOGIC_VERSION_POSTFIX = ':ALGRNAME'
"""Postfix that tells us the logic version"""
