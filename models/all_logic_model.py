from os import path
from logging import getLogger
from glob import glob
from dbinteraction.logicDB.macro import Macro
from dbinteraction.logicDB.macro_device import Macro_Device
from dbinteraction.logicDB.macro_ignore import Macro_Ignore
from dbinteraction.logicDB.macro_state import Macro_State
from dbinteraction.logicDB.zignoremacro import ZIgnoreMacro
from models.prepped_macro import PreppedMacro
from models.prepped_macro_state import PreppedMacroState
from dbinteraction.mps_config import MPSConfig
from sqlalchemy import sql, select, text
import models.all_faults_model as all_faults_model


class AllLogicModel:
    """
    author Evren Keskin
    ==================================================================================
        LogicDB accesses the logic database to get macro data
        and creates a single dictionary of preppedMacro objects,
        which are set up with all relevant info about a macro, including its faults
    ==================================================================================
    """
    def __init__(self, configDB: all_faults_model, accel_type: str, filename=None):
        """Establish logger and establish connection to mps_database."""
        logger = getLogger(__name__)

        if filename and path.exists(filename):
            self.filename = filename
        else:
            if filename:
                logger.error("File does not exist. Using default .db file.")
            self.filename = self.set_filename(accel_type)

        self.configurator = MPSConfig(self.filename)
        self.configDB = configDB
        self.linactype = accel_type

        self.set_prepped_devices(self.linactype)

    def set_filename(self, accel_type):
        """Finds default database filename."""
        if accel_type == 'LCLS':
            return self.set_LCLS_filename()
        else:  # FACET
            return self.set_FACET_filename()

    def set_LCLS_filename(self):
        print('redefining path to default LCLS logic file')
        phys_top = path.expandvars("$EPICS_IOC_TOP")

        # the last version in this directory as I wrote this code...
        # sufficient for testing, and will never be used on lcls-srv01
        # not a good way to make a dynamic fall back for testing well though
        fallBackVersion = '2021-09-23-a'

        filename = glob(phys_top + f'/MpsConfiguration/current/algorithm/{fallBackVersion}/build/mpslogic.sqlite')[0]
        return filename

    def set_FACET_filename(self):
        print('redefining path to default FACET logic file')
        phys_top = path.expandvars("$EPICS_IOC_TOP")

        # the last version in this directory as I wrote this code...
        # sufficient for testing, and will never be used on facet-srv01
        # not a good way to make a dynamic fall back for testing well though
        fallBackVersion = '2023-06-26-a'

        filename = glob(phys_top + f'/MpsConfiguration-FACET/current/\
                        algorithm/{fallBackVersion}/build/mpslogic.sqlite')[0]
        return filename

    def set_prepped_devices(self, accel_type):
        """
         A prepped device holds all information relevant to a macro
        This includes the macro state, ignored status, and the device faults
        """
        self.set_macro_states(accel_type)
        self.set_ignoring_macro_numbers()
        self.initialize_prepped_devices(accel_type)
        self.set_macro_devices()
        self.set_macro_faults()
        self.set_ignored_macros()
        self.set_always_evaluated_macros()

    def set_macro_states(self, accel_type):
        """
        Takes all macro and relevant macro_state information into the macro_and_states list
        """
        if accel_type == 'LCLS':
            self._macro_states = self.configurator.session.query(Macro.macro_number, Macro.name, Macro.is_code,
                                                                 Macro.code, Macro_State.state_number,
                                                                 Macro_State.state_name,
                                                                 Macro_State.rate_enum_gunl, Macro_State.rate_enum_ms,
                                                                 Macro_State.rate_enum_bykik, Macro_State.rate_enum_lhs,
                                                                 Macro_State.rate_enum_gunh, Macro_State.rate_enum_guns,
                                                                 Macro_State.rate_enum_bykiks
                                                                 ).where(Macro.pk == Macro_State.macro_fk).all()
        else:  # FACET
            self._macro_states = self.configurator.session.query(Macro.macro_number, Macro.name, Macro.is_code,
                                                                 Macro.code, Macro_State.state_number,
                                                                 Macro_State.state_name,
                                                                 Macro_State.rate_enum_gunl, Macro_State.rate_enum_ms,
                                                                 Macro_State.rate_enum_lhs
                                                                 ).where(Macro.pk == Macro_State.macro_fk).all()

    def set_ignoring_macro_numbers(self):
        """
        Creates a list for ignored macro numbers and names
        """

        subquery_ignoring_macro = select(ZIgnoreMacro.zmacro, Macro.macro_number).where(
                                         ZIgnoreMacro.zmacro == Macro.pk).alias('ignoring_macro')

        subquery_ignored_macro = select(Macro.macro_number, Macro_Ignore.ignored_when_macro_fk).where(
                                        Macro.pk == Macro_Ignore.macro_fk).alias('ignored_macro')

        joinStatement = sql.expression.outerjoin(subquery_ignoring_macro, subquery_ignored_macro,
                                                 subquery_ignoring_macro.c.zmacro ==
                                                 subquery_ignored_macro.c.ignored_when_macro_fk)

        queryStatement = select(text('ignoring_macro.macro_number'), text('ignored_macro.macro_number')).select_from(
            joinStatement)

        results = self.configurator.session.execute(queryStatement).all()

        self.ignoring_macro_numbers = {}

        for ignoring, ignored in results:
            self.ignoring_macro_numbers[ignoring] = []

        for ignoring, ignored in results:
            if ignored not in self.ignoring_macro_numbers[ignoring]:
                self.ignoring_macro_numbers[ignoring].append(ignored)

    def initialize_prepped_devices(self, accel_type):
        """
        Creates a dictionary of PreppedDevice objects
        The PreppedDevice objects are made with information from all previous db queries
        They are initialized with info from macro states
        All of the macro states are also created and attached to their prepped devices
        """
        preppedDevices = {}
        for ms in self._macro_states:
            preppedDevice = None
            if ms.macro_number in preppedDevices:
                preppedDevice = preppedDevices[ms.macro_number]
            else:
                preppedDevice = PreppedMacro()
                preppedDevice.macro_number = ms.macro_number
                preppedDevice.macro_name = ms.name
                preppedDevice.is_code = ms.is_code
                preppedDevice.code = ms.code
                preppedDevice.is_ignoring = preppedDevice.macro_number in self.ignoring_macro_numbers
                preppedDevices[ms.macro_number] = preppedDevice

            preppedMacroState = PreppedMacroState()
            preppedMacroState.state_number = ms.state_number
            preppedMacroState.state_name = ms.state_name

            if accel_type == 'LCLS':
                preppedMacroState.rate_enums.append(10 if ms.rate_enum_ms == -1 else ms.rate_enum_ms)
                preppedMacroState.rate_enums.append(10 if ms.rate_enum_lhs == -1 else ms.rate_enum_lhs)
                preppedMacroState.rate_enums.append(10 if ms.rate_enum_gunl == -1 else ms.rate_enum_gunl)
                preppedMacroState.rate_enums.append(10 if ms.rate_enum_gunh == -1 else ms.rate_enum_gunh)
                preppedMacroState.rate_enums.append(10 if ms.rate_enum_guns == -1 else ms.rate_enum_guns)
                preppedMacroState.rate_enums.append(10 if ms.rate_enum_bykik == -1 else ms.rate_enum_bykik)
                preppedMacroState.rate_enums.append(10 if ms.rate_enum_bykiks == -1 else ms.rate_enum_bykiks)
            else:  # FACET
                preppedMacroState.rate_enums.append(10 if ms.rate_enum_ms == -1 else ms.rate_enum_ms)
                preppedMacroState.rate_enums.append(10 if ms.rate_enum_gunl == -1 else ms.rate_enum_gunl)
                # different order for where laser heater is on facet
                preppedMacroState.rate_enums.append(10 if ms.rate_enum_lhs == -1 else ms.rate_enum_lhs)

            preppedMacroState.relatedPreppedDevice = preppedDevice
            preppedMacroState.is_ignored = preppedMacroState.state_number < 0
            preppedDevice.add_macro_state(preppedMacroState)

        self.numbersToPreppedDevices = preppedDevices

    def set_macro_devices(self):
        """
        Create a list of device name-macro number pairs
        Only used for pairing faults to the macro
        """
        device_query = self.configurator.session.query(Macro.macro_number, Macro_Device.device_name).where(
                                                       Macro.pk == Macro_Device.macro_fk).order_by(
            Macro_Device.position.asc()).all()

        self._macro_devices = [(macro_number, device_name) for macro_number, device_name in device_query]

    def set_macro_faults(self):
        """
        Using prepped devices, configDB info about faults
        and the device name list
        place faults into the lists of each prepped macro
        """
        for (num, dev) in self._macro_devices:
            fault = self.configDB.get_fault_by_signal(dev)
            # fault.relatedPreppedDevice = self.numbersToPreppedDevices[num]
            self.numbersToPreppedDevices[num].add_fault(fault)

    def set_ignored_macros(self):
        """
        Using the list of ignored numbers to name inquiry results
        We set the list of all macros which are ignored by other macros
        For all macros
        """
        for ignoringMacroNumber in self.ignoring_macro_numbers:
            ignoredMacros = []
            for ignoredMacroNum in self.ignoring_macro_numbers[ignoringMacroNumber]:
                if ignoredMacroNum is not None:
                    ignoredMacro = self.numbersToPreppedDevices[ignoredMacroNum]
                    if ignoredMacro is not None:
                        ignoredMacros.append(ignoredMacro)

            ignoringMacro = self.numbersToPreppedDevices[ignoringMacroNumber]
            ignoringMacro.set_ignored_macros(ignoredMacros)

    def set_always_evaluated_macros(self):
        """
        Creates the list of device macros that are never ignored
        This list unique because unlike the lists of ignored macros that are attached to some macro
        These are never ignored, so they can be found by checking if nothing ignores them
        """
        allMacros = self.numbersToPreppedDevices.values()
        alwaysEvaluatedMacros = []
        for item in allMacros:
            alwaysEvaluatedMacros.append(item)

        for macro1 in allMacros:
            if macro1.is_ignoring is False:
                continue
            for macro2 in macro1.ignored_macros:
                if macro2 in alwaysEvaluatedMacros:
                    alwaysEvaluatedMacros.remove(macro2)
            if macro1 in alwaysEvaluatedMacros:
                alwaysEvaluatedMacros.remove(macro1)

        self.alwaysEvaluatedMacros = alwaysEvaluatedMacros

    def get_always_evaluated_macros_min(self):
        """
        Gets the minimum rate of the current states of all always evaluated device macros
        Defaults to 11, which is 'Ignore Logic'
        """
        min = 11
        for macro in self.alwaysEvaluatedMacros:
            if min > macro.get_current_state().get_min_rate():
                min = macro.get_current_state().get_min_rate()
        min_rate_when_ignoring_inactive = min
        return PreppedMacroState.get_enum_to_val(min_rate_when_ignoring_inactive)

    def get_ignoring_macro_names(self, macroName=None):
        """
        Gets a list of all ignoring macro names based on another given macro name
        This uses the list of ignored macro numbers,
        and checks if that other macro has the parameter macro included in its ignored list
        If that is the case, then this macro is ignored, and so we add the name to the list
        """
        if macroName is None:
            return
        ignoringMacroNames = []
        for num in self.ignoring_macro_numbers:
            for ignored_num in self.ignoring_macro_numbers[num]:
                if (ignored_num is not None and macroName == self.numbersToPreppedDevices[ignored_num].macro_name and
                        self.numbersToPreppedDevices[num].macro_name not in ignoringMacroNames):
                    ignoringMacroNames.append(self.numbersToPreppedDevices[num].macro_name)
        ignoringMacroNames.sort()
        return ignoringMacroNames
