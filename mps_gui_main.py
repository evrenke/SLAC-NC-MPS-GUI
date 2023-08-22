from logging import getLogger
from pydm import Display
from models.all_logic_model import AllLogicModel
from models.all_faults_model import ALLFaultsModel
from models.all_messages_model import AllMessagesModel
from models.logic_table_model import LogicTableModel, MPSItemDelegate
from ui.summary import SummaryUI
from ui.fault import FaultsUI
from ui.logic import LogicUI
from ui.ignore import IgnoreUI
from ui.history import HistoryUI
from ui.recent_faults import RecentFaultsUI
from epics import PV
# from functools import partial
import time
from mps_constants import CURRENT_STATES_POSTFIX, CONFIG_VERSION_POSTFIX, LOGIC_VERSION_POSTFIX


class MpsGuiDisplay(Display, SummaryUI, FaultsUI, LogicUI, IgnoreUI, HistoryUI, RecentFaultsUI):
    """
    author: Evren Keskin
    ===================================================================
    The main program for running the MPS GUI application.
    Gets initialized with various parameters:
    1) the database file paths for configDB
    2) LogicDB path
    3) HistoryDB path
    4) Recent states JSON path
    4) Whether or not to run in CUD mode
    5) Choosing LCLS or FACET
    6) IOC_PREFIX (different between LCLS and FACET)

    Inherits all UI files, and allows control over all 6 tabs of the UI
    Alternatively, ignores this for a simpler CUD Run of 1 of 2 screens
    ===================================================================
    """
    def __init__(self, parent=None, args=[], macros=None, ui_filename=None):

        cud_mode = 'all'
        if 'CUD' in macros:
            cud_mode = macros['CUD']
            cud_mode = cud_mode.lower()

        if 'accel_type' in macros:
            if macros['accel_type'] == 'LCLS':
                if cud_mode == 'summary':
                    ui_filename = 'ui/mps_cud_summary.ui'
                elif cud_mode == 'recent':
                    ui_filename = 'ui/mps_cud_rf.ui'
                else:
                    ui_filename = 'ui/mps_gui_lcls.ui'
            else:  # FACET
                if cud_mode == 'summary':
                    ui_filename = 'ui/mps_cud_summary_facet.ui'
                elif cud_mode == 'recent':
                    ui_filename = 'ui/mps_cud_rf_facet.ui'
                else:
                    ui_filename = 'ui/mps_gui_facet.ui'

        super(MpsGuiDisplay, self).__init__(parent=parent, args=args,
                                            macros=macros, ui_filename=ui_filename)
        self.logger = getLogger(__name__)

        if (macros is not None and
                'configDB_Prefix' in macros and
                'logicDB_Prefix' in macros and
                'IOC_PREFIX' in macros and
                'JSONFILEPATH' in macros and
                'accel_type' in macros):
            configPrefix = macros['configDB_Prefix']
            logicPrefix = macros['logicDB_Prefix']

            self.getConfigModel(macros['IOC_PREFIX'])
            self.getLogicVersion(macros['IOC_PREFIX'])

            configFilename = f'{configPrefix}/{self.config_version}/mpsdb.sqlite3'
            logicFilename = f'{logicPrefix}/{self.logic_version}/build/mpslogic.sqlite'

            if macros['accel_type'] == 'LCLS':
                configFilename = 'mpsdb.sqlite3'
                logicFilename = 'mpslogic.sqlite'
                self.setupLCLS()
            else:
                self.setupFACET()

            myConfigDB = ALLFaultsModel(accel_type=self.linactype, filename=configFilename)
            myLogicDB = AllLogicModel(myConfigDB, accel_type=self.linactype, filename=logicFilename)
            messageModel = AllMessagesModel(wallet=self.historyWalletKey)

            self.model = myLogicDB
            self.messageModel = messageModel
            self.jsonFilePath = macros['JSONFILEPATH']

            # Initialize all screens first

            self.logic_tbl_model = LogicTableModel(self, self.model, self.linactype,
                                                   self.rateList, IOC_PREFIX=macros['IOC_PREFIX'])
            self.delegate = MPSItemDelegate(self)

            if cud_mode == 'summary':
                self.summary_init(is_cud=True)
            elif cud_mode == 'recent':
                self.recent_faults_init(rates_list=self.rateList, is_cud=True)
            else:
                self.summary_init(is_cud=False)
                self.logic_init(self.rateList, macros['IOC_PREFIX'])
                self.fault_init()
                self.ignore_init(self.rateList, macros['IOC_PREFIX'])
                self.history_init()
                self.recent_faults_init(rates_list=self.rateList, is_cud=False)

            if cud_mode != 'recent':
                PV(macros['IOC_PREFIX'] + CURRENT_STATES_POSTFIX, callback=self.update_current_states)

            # Then connect them to PV's or other connections
            if cud_mode != 'summary' and cud_mode != 'recent':
                # logic connections requires a PV connection, which can take some time
                # but a 1 second wait should be a good clear for that time
                time.sleep(1.0)

                self.logic_connections(IOC_PREFIX=macros['IOC_PREFIX'])
                # if not cud_mode:
                self.fault_connections()
                self.summ_connections()
                self.ignore_connections()
                self.history_connections()
                self.recent_faults_connections(IOC_PREFIX=macros['IOC_PREFIX'], is_cud=False)
            if cud_mode == 'recent':
                self.recent_faults_connections(IOC_PREFIX=macros['IOC_PREFIX'], is_cud=True)

            # Allow for a version change based reset of the program
            # Can't test this live since version change is rare
            # But hopefully this allows for version change without crash?
            # Idk how to do this part
            # PV(macros['IOC_PREFIX'] + ':DBVERS', callback=partial(self.resetModel, cud_mode, macros))
            # PV(macros['IOC_PREFIX'] + ':ALGRNAME', callback=partial(self.resetModel, cud_mode, macros))
            # self.resetModel(cud_mode=cud_mode, macros=macros)
        else:
            print('mps_gui_main.py needs config file prefix, logic prefix, ioc prefix, accel type, and json file path')
            print('try again chump')

    def update_current_states(self, value, **kw):
        """
        Update the states shown on the table to the current states from the related PV.
        the parameter 'value' is the array holding all numbers of current states
        """
        value = value.astype('int8')
        self.logic_tbl_model.set_current_states(self.linactype, currentStateNumbers=value)

    # Both of these functions could potentially be a bash parameter...
    # But considering that we only need constants for 2 things its good enough
    # Ideally all constants should be written together in 1 or 2 files tops
    def setupLCLS(self):
        # self.rateList = ["Mech Shutter", "Heater Shutter", "Gun Linac Permit",
        #                  "Gun HXR Permit", "Gun SXR Permit", "BYKIK HXR", "BYKIK SXR"]
        self.rateList = ["Mech Shutter", "Laser Heater", "Gun Linac",
                         "Gun HXR", "Gun SXR", "BYKIK HXR", "BYKIK SXR"]
        self.rateCount = 7
        self.linactype = 'LCLS'
        self.historyWalletKey = 'mps_history'

    def setupFACET(self):
        self.rateList = ["Mech Shutter", "Heater Shutter", "Gun RF Permit"]
        self.rateCount = 3
        self.linactype = 'FACET'
        self.historyWalletKey = 'mps_hist_facet2'

    def getConfigModel(self, IOC_PREFIX: str):
        configPV = PV(IOC_PREFIX + CONFIG_VERSION_POSTFIX)
        self.config_version = configPV.get()

    def getLogicVersion(self, IOC_PREFIX: str):
        logicPV = PV(IOC_PREFIX + LOGIC_VERSION_POSTFIX)
        self.logic_version = logicPV.get()

    def config_version_change_reset(self, value, **kw):
        print('insert a version change table reset here, some forced restart of the whole program')
        self.config_version = value

    def logic_version_change_reset(self, value, **kw):
        print('insert a version change table reset here, some forced restart of the whole program')
        self.logic_version = value

    def resetModel(self, cud_mode, macros, **kw):

        configPrefix = macros['configDB_Prefix']
        logicPrefix = macros['logicDB_Prefix']

        self.getConfigModel(macros['IOC_PREFIX'])
        self.getLogicVersion(macros['IOC_PREFIX'])

        configFilename = f'{configPrefix}/{self.config_version}/mpsdb.sqlite3'
        logicFilename = f'{logicPrefix}/{self.logic_version}/build/mpslogic.sqlite'

        configFilename = 'mpsdb.sqlite3'
        logicFilename = 'mpslogic.sqlite'

        myConfigDB = ALLFaultsModel(filename=configFilename)
        myLogicDB = AllLogicModel(myConfigDB, accel_type=macros['accel_type'], filename=logicFilename)
        messageModel = AllMessagesModel()

        self.model = myLogicDB
        self.messageModel = messageModel
        self.jsonFilePath = macros['JSONFILEPATH']

        self.logic_tbl_model = LogicTableModel(self, self.model, IOC_PREFIX=macros['IOC_PREFIX'])
        self.delegate = MPSItemDelegate(self)

        # if cud_mode == 'Summary':
        #     self.summary_init(is_cud=True)
        # elif cud_mode == 'All':
        #     self.summary_init(is_cud=False)
        #     self.logic_init()
        #     self.fault_init()
        #     self.ignore_init()
        #     # self.history_init()
        #     # self.recent_faults_init()
        # # elif cud_mode == 'Recent Faults':
        #     # self.recent_faults_init()

        # # Then connect them to PV's or other connections
        # if cud_mode == 'All':
        #     # logic connections requires a PV connection, which can take some time
        #     # but a 1 second wait should be a good clear for that time
        #     time.sleep(1.0)

        #     self.logic_connections(IOC_PREFIX=macros['IOC_PREFIX'])
        #     # if not cud_mode:
        #     self.fault_connections()
        #     # self.summ_connections()
        #     self.ignore_connections()
        #     # self.history_connections()
        #     # self.recent_faults_connections(IOC_PREFIX=macros['IOC_PREFIX'], is_cud=False)
        # # if cud_mode == 'Recent Faults':
        #     # self.recent_faults_connections(IOC_PREFIX=macros['IOC_PREFIX'], is_cud=True)
