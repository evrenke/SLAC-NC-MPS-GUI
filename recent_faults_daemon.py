from models.all_faults_model import ALLFaultsModel
from models.all_logic_model import AllLogicModel
from epics import PV
import sys
from datetime import datetime
from threading import Thread
import time
import json
from models.prepped_macro_state import PreppedMacroState
# from functools import partial
from mps_constants import RECENT_FAULTS_MAX, CURRENT_STATES_POSTFIX, CONFIG_VERSION_POSTFIX, LOGIC_VERSION_POSTFIX
import threading
import queue


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
        if sys.argv is not None and sys.argv[1] is not None and sys.argv[2] is not None and sys.argv[3] is not None:
            self.configPrefix = sys.argv[1]
            self.logicPrefix = sys.argv[2]
            self.IOC_PREFIX = sys.argv[3]
            self.jsonFilename = sys.argv[4]
            self.linactype = sys.argv[5]

            self.configPV = PV(self.IOC_PREFIX + CONFIG_VERSION_POSTFIX)
            self.logicPV = PV(self.IOC_PREFIX + LOGIC_VERSION_POSTFIX)
            self.configPV.wait_for_connection()
            self.logicPV.wait_for_connection()

            self.config_version = self.configPV.get()
            self.logic_version = self.logicPV.get()

            self.resetModel()

            self.newValuesQueue = queue.Queue()

            # creating a thread to update JSON
            Recent_States_Thread = Thread(target=self.recent_states_daemon_thread)

            # starting of thread T
            Recent_States_Thread.start()

    # creating a function
    def recent_states_daemon_thread(self):

        self.lastValuesList = None
        self.isUpdatingJSON = False
        self.wantsToUpdateAfterUpdate = False
        PV(self.IOC_PREFIX + CURRENT_STATES_POSTFIX, callback=self.recent_states_check)

        # I know, some call me a programming genius, a prodigy and visionary
        while True:
            # this is daemon thread with update checking
            while not self.newValuesQueue.empty():
                self.add_latest_states(self.newValuesQueue.get())
            time.sleep(5)  # 5 seconds wait completely arbitraty, I just want to avoid melting slac servers
        return

    def append_to_json(self, all_new_data):

        # Using the threading method from this example
        # https://stackoverflow.com/questions/10525185/python-threading-how-do-i-lock-a-thread

        lock = threading.Lock()
        with lock:
            # print('locked writing to json file')
            file_path = self.jsonFilename

            with open(file_path, 'r') as file:
                # First we load existing data into a dict.
                file_data = json.load(file)

            with open(file_path, 'w') as file:
                # Join new_data with file_data inside emp_details
                for new_data in all_new_data:
                    file_data['recent faults'].append(new_data)

                # Check if the number of items is past a specified limit
                # Over the limit of RECENT_FAULTS_MAX, have to remove items
                while len(file_data['recent faults']) > RECENT_FAULTS_MAX:
                    file_data['recent faults'].pop(0)
                # Sets file's current position at offset.
                # file.seek(0)
                # convert back to json.
                json.dump(file_data, file, indent=4)

    def recent_states_check(self, value, **kw):
        if (self.config_version != self.configPV.get() or
           self.logic_version != self.logicPV.get()):
            self.resetModel()

        self.newValuesQueue.put(value)

        # self.add_latest_states(value)

    def add_latest_states(self, value):
        """
        Add the latest states
        start by initializing an existing list of states
        compared differences are new states for macros, and should be added
        """

        value = value.astype('int8')
        if self.lastValuesList is None:  # on the first iteration, there is no previous list
            self.lastValuesList = value
        else:
            # print('getting real')
            changeTime = datetime.now()
            changeTime = changeTime.strftime('%Y-%m-%d %H:%M:%S')
            lastValues = self.lastValuesList

            # First, find each state in the list that is different from the previous list
            # Then, for each difference of states, create an item of that new state, the related macro,
            # and the date of the change of the state pv
            all_new_data = []
            for index, old_state_num in enumerate(lastValues):
                new_state_num = value[index]
                if int(old_state_num) != int(new_state_num):
                    try:
                        macro = self.myLogicDB.numbersToPreppedDevices[index]
                        state = macro.get_state_by_state_number(new_state_num)

                        if state is not None:  # if the models used dont match what the current state PV expects, ignore
                            if self.linactype == 'LCLS':
                                new_data = {'statename': state.state_name,
                                            'staterates': [PreppedMacroState.get_enum_to_val(state.get_min_rate()),
                                                           PreppedMacroState.get_enum_to_val(state.rate_enums[0]),
                                                           PreppedMacroState.get_enum_to_val(state.rate_enums[1]),
                                                           PreppedMacroState.get_enum_to_val(state.rate_enums[2]),
                                                           PreppedMacroState.get_enum_to_val(state.rate_enums[3]),
                                                           PreppedMacroState.get_enum_to_val(state.rate_enums[4]),
                                                           PreppedMacroState.get_enum_to_val(state.rate_enums[5]),
                                                           PreppedMacroState.get_enum_to_val(state.rate_enums[6])],
                                            'macro': macro.macro_name,
                                            'date': changeTime
                                            }
                            else:  # FACET
                                new_data = {'statename': state.state_name,
                                            'staterates': [PreppedMacroState.get_enum_to_val(state.get_min_rate()),
                                                           PreppedMacroState.get_enum_to_val(state.rate_enums[0]),
                                                           PreppedMacroState.get_enum_to_val(state.rate_enums[1]),
                                                           PreppedMacroState.get_enum_to_val(state.rate_enums[2])],
                                            'macro': macro.macro_name,
                                            'date': changeTime
                                            }

                            all_new_data.append(new_data)
                    except KeyError:
                        continue

            self.append_to_json(all_new_data=all_new_data)
            self.lastValuesList = value

    def resetModel(self):
        configFilename = f'{self.configPrefix}/{self.config_version}/mpsdb.sqlite3'
        logicFilename = f'{self.logicPrefix}/{self.logic_version}/build/mpslogic.sqlite'

        print('resetting recent faults daemon')
        print(configFilename)
        print(logicFilename)

        self.myConfigDB = ALLFaultsModel(accel_type=self.linactype, filename=configFilename)
        self.myLogicDB = AllLogicModel(self.myConfigDB, accel_type=self.linactype, filename=logicFilename)


if __name__ == '__main__':
    RecentFaultsDaemon()
