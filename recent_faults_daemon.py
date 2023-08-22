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


class RecentFaultsDaemon():
    """
    author: Evren Keskin
    =====================================================================
    This is a sibling program separate from MPS GUI, which watches the current states PV
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

            self.config_version = self.getConfigModel()
            self.logic_version = self.getLogicVersion()

            self.resetModel()

            # creating a thread to update JSON
            Recent_States_Thread = Thread(target=self.recent_states_daemon_thread)

            print('starting endless thread')

            # print(self.config_version)
            # print(self.logic_version)

            # starting of thread T
            Recent_States_Thread.start()

    # creating a function
    def recent_states_daemon_thread(self):
        # self.update_count = 0

        self.lastStateSituationList = None
        self.isUpdatingJSON = False
        self.wantsToUpdateAfterUpdate = False
        PV(self.IOC_PREFIX + CURRENT_STATES_POSTFIX, callback=self.recent_states_check)

        # I know, some call me a programming genius, a prodigy and visionary
        while True:
            # this is daemon thread with update checking
            time.sleep(20)
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
                json.dump(file_data, file, indent=3)

    def recent_states_check(self, value, **kw):
        if (self.config_version != self.getConfigModel() or
           self.logic_version != self.getLogicVersion()):
            self.resetModel()

        self.add_latest_states(value)

    def add_latest_states(self, value):
        """
        Add the latest states
        start by initializing an existing list of states
        compared differences are new states for macros, and should be added
        """

        # print('adding latest states check')
        changeTime = datetime.now()
        changeTime = changeTime.strftime('%Y-%m-%d %H:%M:%S')
        value = value.astype('int8')
        if self.lastStateSituationList is None:
            self.lastStateSituationList = value
        elif not self.isUpdatingJSON:
            self.isUpdatingJSON = True
            # First, find each state in the list that is different from the previous list
            # Then, for each difference of states, create an item of that new state, the related macro,
            # and the date of the change of the state pv
            all_new_data = []
            for index, state_num in enumerate(self.lastStateSituationList):
                if int(state_num) != int(value[index]):
                    macro = self.myLogicDB.numbersToPreppedDevices[index]

                    state = macro.get_state_by_state_number(state_num)

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

            # print('appending to json ', all_new_data)
            self.append_to_json(all_new_data=all_new_data)
            self.lastStateSituationList = value
            self.isUpdatingJSON = False
            # print('done with an update')
            if self.wantsToUpdateAfterUpdate:
                self.wantsToUpdateAfterUpdate = False
                self.add_latest_states(value)
            # this is not the first call, check what is changed about the list of states
        elif not self.wantsToUpdateAfterUpdate:
            # print('waiting do another update')
            self.wantsToUpdateAfterUpdate = True

        # self.update_count += 1

    def resetModel(self):
        configFilename = f'{self.configPrefix}/{self.config_version}/mpsdb.sqlite3'
        logicFilename = f'{self.logicPrefix}/{self.logic_version}/build/mpslogic.sqlite'

        print(configFilename)
        print(logicFilename)

        # TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY
        # TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY
        # if self.linactype == 'LCLS':
        #     configFilename = 'mpsdb.sqlite3'
        #     logicFilename = 'mpslogic.sqlite'

        self.myConfigDB = ALLFaultsModel(accel_type=self.linactype, filename=configFilename)
        self.myLogicDB = AllLogicModel(self.myConfigDB, accel_type=self.linactype, filename=logicFilename)

    def getConfigModel(self):
        self.configPV = PV(self.IOC_PREFIX + CONFIG_VERSION_POSTFIX)
        return self.configPV.get()

    def getLogicVersion(self):
        self.logicPV = PV(self.IOC_PREFIX + LOGIC_VERSION_POSTFIX)
        return self.logicPV.get()


RecentFaultsDaemon()
