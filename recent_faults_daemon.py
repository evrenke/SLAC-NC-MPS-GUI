import time
from datetime import datetime
from argparse import ArgumentParser
from threading import Lock, Thread
from epics import PV
import mps_constants as const
from models.all_logic_model import AllLogicModel
from models.all_faults_model import ALLFaultsModel
from models.prepped_macro_state import PreppedMacroState
from dbinteraction.mps_config import MPSConfig
from dbinteraction.recentStatesDB.recent_sql import do_single_insert


class RecentFaultsDaemon():
    """
    author: Evren Keskin
    =====================================================================
    This is a sibling program separate from NC MPS GUI, which watches the current states PV
    This PV has a list of all macro's current states, indexed by their macro numbers from the model
    Each change on it tells us about a change of states
    This program writes to a JSON a log of the recent X number of changes
    Allowing a quick to access list of the recent changes to states

    =====================================================================

    It relies on the model matching what the PV gives,
    meaning it has to deal with version changes on the run
    """
    def __init__(self):
        parser = ArgumentParser(prog="Recent Faults Daemon")
        parser.add_argument("configPrefix")
        parser.add_argument("logicPrefix")
        parser.add_argument("IOC_PREFIX")
        parser.add_argument("recentStatesDBPath")
        parser.add_argument("linacType", default="LCLS", choices=["LCLS", "FACET"])
        self.args = parser.parse_args()

        self.ioc_pre = self.args.IOC_PREFIX

        self.configPV = PV(self.ioc_pre + const.CONFIG_VERSION_POSTFIX)
        self.logicPV = PV(self.ioc_pre + const.LOGIC_VERSION_POSTFIX)
        self.configPV.wait_for_connection()
        self.logicPV.wait_for_connection()

        self.resetModel()
        self.conf = MPSConfig(self.args.recentStatesDBPath)

        self.queued_states = []
        states_pv = PV(self.ioc_pre + const.CURRENT_STATES_POSTFIX)
        self.prev_states = states_pv.value.astype('int8')
        states_pv.add_callback(self.recent_states_check, run_now=True)

        self.lock = Lock()
        recent_states_thread = Thread(target=self.recent_states_daemon_thread)
        recent_states_thread.start()

    # creating a function
    def recent_states_daemon_thread(self):
        # I know, some call me a programming genius, a prodigy and visionary
        while True:
            # this is daemon thread with update checking
            while self.queued_states:
                with self.lock:
                    self.add_latest_states(*self.queued_states.pop(0))
            time.sleep(5)  # 5 seconds wait completely arbitraty, I just want to avoid melting slac servers
        return

    def recent_states_check(self, value, **kw):
        if (self.config_version != self.configPV.get() or
           self.logic_version != self.logicPV.get()):
            self.resetModel()

        value = value.astype('int8')

        changeTime = datetime.now()
        changeTime = changeTime.strftime('%Y-%m-%d %H:%M:%S')
        self.queued_states.append((value, changeTime))

    def add_latest_states(self, new_states, timestamp):
        """
        Add the latest states
        start by initializing an existing list of states
        compared differences are new states for macros, and should be added
        """
        diff_states = [(i, n) for i, (p, n) in enumerate(zip(self.prev_states, new_states)) if p != n]

        # First, find each state in the list that is different from the previous list
        # Then, for each difference of states, create an item of that new state, the related macro,
        # and the date of the change of the state pv
        for i, new_state in diff_states:
            try:
                macro = self.myLogicDB.numbersToPreppedDevices[i]
                state = macro.get_state_by_state_number(new_state)
                if not state:
                    continue

                params = {'date_param': timestamp,
                          'macro_name_param': macro.macro_name,
                          'state_name_param': state.state_name,
                          'min_rate_param': PreppedMacroState.get_enum_to_val(state.get_min_rate()),
                          'rate_ms_param': PreppedMacroState.get_enum_to_val(state.rate_enums[0])}

                if self.args.linacType == "LCLS":
                    params['rate_lhs_param'] = PreppedMacroState.get_enum_to_val(state.rate_enums[1])
                    params['rate_gunl_param'] = PreppedMacroState.get_enum_to_val(state.rate_enums[2])
                    params['rate_gunh_param'] = PreppedMacroState.get_enum_to_val(state.rate_enums[3])
                    params['rate_guns_param'] = PreppedMacroState.get_enum_to_val(state.rate_enums[4])
                    params['rate_bykik_param'] = PreppedMacroState.get_enum_to_val(state.rate_enums[5])
                    params['rate_bykiks_param'] = PreppedMacroState.get_enum_to_val(state.rate_enums[6])
                elif self.args.linacType == "FACET":
                    params['rate_gunl_param'] = PreppedMacroState.get_enum_to_val(state.rate_enums[1])
                    params['rate_lhs_param'] = PreppedMacroState.get_enum_to_val(state.rate_enums[2])

                with self.conf.Session() as session:
                    do_single_insert(session=session, **params)

            except KeyError:
                continue

        self.prev_states = new_states

    def resetModel(self):
        self.config_version = self.configPV.value
        self.logic_version = self.logicPV.value

        configFilename = f'{self.args.configPrefix}/{self.config_version}/mpsdb.sqlite3'
        logicFilename = f'{self.args.logicPrefix}/{self.logic_version}/build/mpslogic.sqlite'

        print('resetting recent faults daemon')
        print(configFilename)
        print(logicFilename)

        self.myConfigDB = ALLFaultsModel(accel_type=self.args.linacType, filename=configFilename)
        self.myLogicDB = AllLogicModel(self.myConfigDB, accel_type=self.args.linacType, filename=logicFilename)


if __name__ == '__main__':
    RecentFaultsDaemon()
