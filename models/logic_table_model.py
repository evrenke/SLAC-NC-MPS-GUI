from logging import getLogger
from platform import system
from qtpy.QtCore import (Qt, QModelIndex, QAbstractTableModel,
                         QEvent, QSortFilterProxyModel)
from qtpy.QtWidgets import (QStyledItemDelegate, QApplication, QToolTip)
from .enums import Statuses
from models.all_logic_model import AllLogicModel
from models.prepped_macro_state import PreppedMacroState
from epics import PV
from datetime import datetime
import numpy
from mps_constants import FROM_1970_TO_1990_IN_SECONDS, BYPASS_FAULT_NUMBERS_POSTFIX, BYPASS_SECONDS_POSTFIX


class LogicTableModel(QAbstractTableModel):
    """
    author: Evren Keskin
    ===================================================================
    This is a table model that holds the state logic information for display.
    It is used as a connection between the UI display in logic_ui,
    and the models of retrieved data from AllLogicModel.
    It holds the rows of data that is used for table display in '_data'.
    For now, it is hard coded for LCLS use, but can easily be adapted for more flexibility
    ===================================================================

    The most important functions are
    __init__: used to create the table header, the hidden columns, and initialize what the user first sees
    set_data: used to set the table row data based on AllLogicModel info. This is what the user sees
    update_current_states: gets the retrieved list of current states for each macro,
        which is used to update the data to the accurate states for the user
    """
    logger = getLogger(__name__)

    def __init__(self, parent, model: AllLogicModel, accel_type: str, rates_list=None, IOC_PREFIX=None):
        super(LogicTableModel, self).__init__(parent)
        self.model = model

        self.hdr_lst = (["Name", "State", "Min Rate"])

        self.hdr_lst += rates_list

        # Hidden columns used for information about the data in the row
        self.hdr_lst += ["Ignored", "Macro Number", "Bypassed", "Bypass Exp Date", "Is Ignoring",
                         "Min Rate From All", "Is Condition", "Always Evaluated"]

        self.iind = self.hdr_lst.index("Ignored")
        self.numind = self.hdr_lst.index("Macro Number")
        self.bind = self.hdr_lst.index("Bypassed")
        self.beind = self.hdr_lst.index("Bypass Exp Date")
        self.miind = self.hdr_lst.index("Is Ignoring")
        self.mmrind = self.hdr_lst.index("Min Rate From All")
        self.cind = self.hdr_lst.index("Is Condition")
        self.aeind = self.hdr_lst.index("Always Evaluated")

        self.conind = [self.iind, self.numind, self.bind, self.beind, self.miind, self.mmrind, self.cind, self.aeind]

        self._data = []  # table data, which will hold inputs from database data
        self.status = []  # used to determine if a data row is in a warning or red state to show on summary
        self.channels = []  # channels used to copy the name of the logic item easily with middle click

        self.bypass_seconds_PV = PV(IOC_PREFIX + BYPASS_SECONDS_POSTFIX)
        self.bypassed_faults_PV = PV(IOC_PREFIX + BYPASS_FAULT_NUMBERS_POSTFIX)

        self.set_initial_data(accel_type)

        # Two flag system to stagger updates in case the current states are asked to update before an update is finished
        self.isBeingUpdated = False
        self.isWaitingToUpdateAgain = False

    def rowCount(self, index: QModelIndex = QModelIndex()):
        """Return the number of rows in the model."""
        return len(self._data)

    def columnCount(self, index: QModelIndex = QModelIndex()):
        """Return the number of columns in the model."""
        return len(self.hdr_lst)

    def data(self, index: QModelIndex, role: Qt.ItemDataRole):
        """Return the index's text, alignment, background color,
        OR foreground color."""
        if not index.isValid():
            return
        elif role == Qt.DisplayRole:
            return str(self._data[index.row()][index.column()])
        elif role == Qt.TextAlignmentRole and 0 < index.column():
            return Qt.AlignCenter
        elif role == Qt.BackgroundRole and 0 < index.column():
            return Statuses.BGD.brush()
        elif role == Qt.ForegroundRole:
            row = index.row()
            col = index.column()
            txt = index.data()

            # A rate column, needs to be colored by rate
            if (2 <= col < self.conind[0] or col == self.mmrind):
                if txt == '0 Hz' or txt == 'Invalid' or txt == 'Unknown':
                    return Statuses.RED.brush()
                if txt == '1 Hz' or txt == '10 Hz' or txt == '30 Hz' or txt == '60 Hz':
                    if self.model.linactype == 'LCLS':
                        return Statuses.YEL.brush()
                    elif txt == '30 Hz':  # FACET
                        return Statuses.GRN.brush()
                    return Statuses.YEL.brush()
                if (txt == '120 Hz' or txt == 'Single Shot'
                        or txt == 'Burst Mode' or txt == '--' or txt == 'Ignore Logic'):
                    return Statuses.GRN.brush()

            elif col == self.iind and txt == 'Y':
                return Statuses.YEL.brush()

            elif col == self.beind:
                # Check if ANY fault is bypassed
                lowestDuration = None

                # To set the duration, we find the lowest bypass duration of any of the faults
                # So, if a code macro were to have many various durations, the lowest is shown
                bypassed_faults = self.bypassed_faults_PV.value
                seconds = self.bypass_seconds_PV.value
                for fault in self.model.numbersToPreppedDevices[self._data[row][self.numind]].faults:
                    if fault.fault_number in bypassed_faults:
                        second_index = numpy.where(bypassed_faults == fault.fault_number)[0]
                        if lowestDuration is None or lowestDuration > seconds[second_index][0]:
                            lowestDuration = seconds[second_index][0] + FROM_1970_TO_1990_IN_SECONDS
                if lowestDuration is not None:
                    remainingTime = lowestDuration - (int(datetime.now().timestamp()))
                    if (remainingTime < 60 * 60):  # within 1 hour there is an expiration
                        return Statuses.RED.brush()
                    if (remainingTime < 24 * 60 * 60):  # within 1 day there is an expiration
                        return Statuses.YEL.brush()
                    # if (remainingTime <  7 * 24 * 60 * 60): # within a week there is an expiration
                    #     return Statuses.YEL.brush()
                return Statuses.GRN.brush()   # expiration more than a week

            elif col != 0:  # catch all that makes all non-name remainders white
                return Statuses.GRN.brush()

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: Qt.ItemDataRole):
        """Set the horizontal header's text."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.hdr_lst[section]

    def set_initial_data(self, accel_type):
        """
        Set initial data for each row, based on the preppedDeviceMacro.
        Populate each logic item with the
        description, the PV name, and default values for bypass, ignore,
        and active cells.
        """
        self._data = []
        self.status = []

        seconds = self.bypass_seconds_PV.value
        bypassed_faults = self.bypassed_faults_PV.value

        for index, macro_num in enumerate(self.model.numbersToPreppedDevices):
            cur_state = self.model.numbersToPreppedDevices[macro_num].get_current_state()
            lst = [cur_state.state_name] * len(self.hdr_lst)
            lst[0] = self.model.numbersToPreppedDevices[macro_num].macro_name
            lst[1] = cur_state.state_name
            lst[2] = PreppedMacroState.get_enum_to_val(cur_state.get_min_rate())
            lst[3] = PreppedMacroState.get_enum_to_val(cur_state.rate_enums[0])
            lst[4] = PreppedMacroState.get_enum_to_val(cur_state.rate_enums[1])
            lst[5] = PreppedMacroState.get_enum_to_val(cur_state.rate_enums[2])
            if accel_type == 'LCLS':
                lst[6] = PreppedMacroState.get_enum_to_val(cur_state.rate_enums[3])
                lst[7] = PreppedMacroState.get_enum_to_val(cur_state.rate_enums[4])
                lst[8] = PreppedMacroState.get_enum_to_val(cur_state.rate_enums[5])
                lst[9] = PreppedMacroState.get_enum_to_val(cur_state.rate_enums[6])
            lst[self.numind] = macro_num
            if cur_state.is_ignored:
                lst[self.iind] = 'Y'
            else:
                lst[self.iind] = 'N'

            # For checking bypassing, we need to check the fault id in the bypassed list
            hasAnyBypassedFault = False
            lowestDuration = None
            for fault in self.model.numbersToPreppedDevices[macro_num].faults:
                if fault.fault_number in bypassed_faults:
                    hasAnyBypassedFault = True
                    second_index = numpy.where(bypassed_faults == fault.fault_number)[0]
                    if lowestDuration is None or lowestDuration < seconds[second_index][0]:
                        lowestDuration = seconds[second_index][0] + FROM_1970_TO_1990_IN_SECONDS

            if not hasAnyBypassedFault:
                lst[self.bind] = 'N'
                lst[self.beind] = 'None'
            else:
                # To set the duration, we find the lowest bypass duration of any of the faults
                # So, if a code macro were to have many various durations, the lowest would be shown
                lst[self.bind] = 'Y'
                lst[self.beind] = datetime.fromtimestamp(lowestDuration)

            if (self.model.numbersToPreppedDevices[macro_num].is_ignoring and
                    cur_state.state_number == -55):
                lst[self.miind] = 'Y'
            else:
                lst[self.miind] = 'N'

            lst[self.mmrind] = self.model.numbersToPreppedDevices[macro_num].get_min_rate_from_ignored()

            lst[self.cind] = 'Y' if self.model.numbersToPreppedDevices[macro_num].is_ignoring else 'N'
            lst[self.aeind] = 'N'

            self._data.append(lst)

            if (cur_state.get_min_rate() == -1 or
                    cur_state.get_min_rate() == 2 or
                    cur_state.get_min_rate() == 3 or
                    cur_state.get_min_rate() == 8 or
                    cur_state.get_min_rate() == 10):
                self.status.append(Statuses.GRN)
            elif cur_state.get_min_rate() == 0 or cur_state.get_min_rate() == 1 or cur_state.get_min_rate() == 9:
                self.status.append(Statuses.RED)
            elif (cur_state.get_min_rate() == 4 or
                  cur_state.get_min_rate() == 5 or
                  cur_state.get_min_rate() == 6 or
                  cur_state.get_min_rate() == 7):
                self.status.append(Statuses.YEL)

            self.channels.append(self.model.numbersToPreppedDevices[macro_num].macro_name)

            self.dataChanged.emit(self.index(index, 1),
                                  self.index(index, self.conind[-1] - 1))

        self.addAlwaysEvaluatedCondition(accel_type)

    def addAlwaysEvaluatedCondition(self, accel_type):
        """
        Append a special case non-macro
        The 'Always Evaluated' condition
        Its used only for the Ignore Logic screen
        to show the macros which do not have any ignore conditions
        """
        lst = ['You Should Not See This'] * len(self.hdr_lst)
        lst[0] = 'Always Evaluated'
        lst[1] = 'You Should Not See This'
        lst[2] = '--'
        lst[3] = '--'
        lst[4] = '--'
        lst[5] = '--'
        if accel_type == 'LCLS':
            lst[6] = '--'
            lst[7] = '--'
            lst[8] = '--'
            lst[9] = '--'
        lst[self.numind] = -42069  # special key for the always evaluated condition
        lst[self.iind] = 'Y'
        lst[self.bind] = 'N'
        lst[self.miind] = '--'
        # Important line:
        lst[self.mmrind] = self.model.get_always_evaluated_macros_min()

        lst[self.cind] = 'Y'
        # Important line:
        lst[self.aeind] = 'Y'

        self._data.append(lst)
        self.status.append(Statuses.GRN)

    def set_updated_data(self, accel_type):
        """
        Set initial data for each row, based on the preppedDeviceMacro.
        Populate each logic item with the
        description, the PV name, and default values for bypass, ignore,
        and active cells.
        """
        seconds = self.bypass_seconds_PV.value
        bypassed_faults = self.bypassed_faults_PV.value

        for index, macro_num in enumerate(self.model.numbersToPreppedDevices):
            cur_state = self.model.numbersToPreppedDevices[macro_num].get_current_state()
            self._data[index][1] = cur_state.state_name
            self._data[index][2] = PreppedMacroState.get_enum_to_val(cur_state.get_min_rate())
            self._data[index][3] = PreppedMacroState.get_enum_to_val(cur_state.rate_enums[0])
            self._data[index][4] = PreppedMacroState.get_enum_to_val(cur_state.rate_enums[1])
            self._data[index][5] = PreppedMacroState.get_enum_to_val(cur_state.rate_enums[2])
            if accel_type == 'LCLS':
                self._data[index][6] = PreppedMacroState.get_enum_to_val(cur_state.rate_enums[3])
                self._data[index][7] = PreppedMacroState.get_enum_to_val(cur_state.rate_enums[4])
                self._data[index][8] = PreppedMacroState.get_enum_to_val(cur_state.rate_enums[5])
                self._data[index][9] = PreppedMacroState.get_enum_to_val(cur_state.rate_enums[6])
            if cur_state.is_ignored:
                self._data[index][self.iind] = 'Y'
            else:
                self._data[index][self.iind] = 'N'

            # For checking bypassing, we need to check the fault id in the bypassed list
            hasAnyBypassedFault = False
            lowestDuration = None
            for fault in self.model.numbersToPreppedDevices[macro_num].faults:
                if fault.fault_number in bypassed_faults:
                    hasAnyBypassedFault = True
                    second_index = numpy.where(bypassed_faults == fault.fault_number)[0]
                    if lowestDuration is None or lowestDuration < seconds[second_index][0]:
                        lowestDuration = seconds[second_index][0] + FROM_1970_TO_1990_IN_SECONDS

            if not hasAnyBypassedFault:
                self._data[index][self.bind] = 'N'
                self._data[index][self.beind] = 'None'
            else:
                # To set the duration, we find the lowest bypass duration of any of the faults
                # So, if a code macro were to have many various durations, the lowest would be shown
                self._data[index][self.bind] = 'Y'
                self._data[index][self.beind] = datetime.fromtimestamp(lowestDuration)

            if self.model.numbersToPreppedDevices[macro_num].is_ignoring and cur_state.state_number == -55:
                self._data[index][self.miind] = 'Y'
            else:
                self._data[index][self.miind] = 'N'

            self._data[index][self.mmrind] = self.model.numbersToPreppedDevices[macro_num].get_min_rate_from_ignored()

            self._data[index][self.cind] = 'Y' if self.model.numbersToPreppedDevices[macro_num].is_ignoring else 'N'

            if (cur_state.get_min_rate() == -1 or
                    cur_state.get_min_rate() == 2 or
                    cur_state.get_min_rate() == 3 or
                    cur_state.get_min_rate() == 8 or
                    cur_state.get_min_rate() == 10):
                self.status[index] = Statuses.GRN
            elif cur_state.get_min_rate() == 0 or cur_state.get_min_rate() == 1 or cur_state.get_min_rate() == 9:
                self.status[index] = Statuses.RED
            elif (cur_state.get_min_rate() == 4 or
                  cur_state.get_min_rate() == 5 or
                  cur_state.get_min_rate() == 6 or
                  cur_state.get_min_rate() == 7):
                self.status[index] = Statuses.YEL

            if accel_type == 'FACET' and cur_state.get_min_rate() == 6:  # 30 Hz
                self.status[index] = Statuses.GRN

            self.dataChanged.emit(self.index(index, 1),
                                  self.index(index, self.conind[-1] - 1))

        self._data[len(self.model.numbersToPreppedDevices)][self.mmrind] = self.model.get_always_evaluated_macros_min()

    def set_current_states(self, accel_type: str, currentStateNumbers):
        """
        Called when the Current States PV info changes.
        Sets the new current states of the macro list from the macro model
        and resets all data of the table model
        """
        if self.isBeingUpdated is False:
            self.isBeingUpdated = True
            # print('updating current logic states')

            for macro in self.model.numbersToPreppedDevices.values():
                # current states are indexed by their related macros
                thisMacrosCurrentStateNumber = currentStateNumbers[macro.macro_number]
                macro.set_current_state(thisMacrosCurrentStateNumber)

            self.set_updated_data(accel_type)
            self.isBeingUpdated = False
            if self.isWaitingToUpdateAgain is True:
                self.isWaitingToUpdateAgain = False
                self.set_current_states(accel_type, currentStateNumbers)
        elif self.isWaitingToUpdateAgain is False:
            # Tried, and failed an update, so try to update again
            # print('failed a current state update, will call update when current process finishes')
            self.isWaitingToUpdateAgain = True

    def less_than(self, left: QModelIndex, right: QModelIndex, sortorder: Qt.SortOrder):
        """Called by MPSSortFilterProxyModel to sort rows based on the
        app's status."""
        left_state = left.data()
        right_state = right.data()

        # Check for errors
        # Timing issues can cause this to be used
        # Otherwise it shouldn't be possible
        # if left_state is None and right_state is not None:
        #     print('ITS ALL NONE FOR ', left.row(), ' ', left.column(), ' and ', right.row(), ' ', right.column())
        #     return False
        # elif left_state is not None and right_state is None:
        #     print('RIGHT IS NONE FOR ', left.row(), ' ', left.column(), ' and ', right.row(), ' ', right.column())
        #     return True
        # elif left_state is None and right_state is None:
        #     print('LEFT IS NONE FOR ', left.row(), ' ', left.column(), ' and ', right.row(), ' ', right.column())
        #     return False

        # Being not ignored is always more important than being ignored
        # So when the table is sorted, asceng or descending, the not ignored data always takes priority
        if (left.column() != self.iind and left.column() != self.beind and
                left.column() != self.miind and left.column() != self.mmrind):
            if (left.siblingAtColumn(self.iind).data() == 'N' and right.siblingAtColumn(self.iind).data() == 'Y'):
                return sortorder == Qt.AscendingOrder
            if (right.siblingAtColumn(self.iind).data() == 'N' and left.siblingAtColumn(self.iind).data() == 'Y'):
                return sortorder != Qt.AscendingOrder

        if left.column() > 1 and left.column() < self.conind[0]:
            return PreppedMacroState.get_val_to_enum(left_state) < PreppedMacroState.get_val_to_enum(right_state)

        return left_state < right_state

    def filter_accepts_row(self, row: int, parent: QModelIndex, filters: dict):
        """
        Called by MPSSortFilterProxyModel to filter out rows based on
        the table's needs.
        """
        for col, text in filters.items():
            if col == 2:
                # .faulted() is from enums.py
                # It will tell us if the item should be shown based on its min rate status
                if not self.status[row].faulted():
                    return False
            elif col == self.numind:
                # Check if the text parameter from filters is a number
                # Use the text to decide which list of ignored conditions to look at
                # This decides if this item should be accepted or not
                ignored_nums = []

                if not text.isdecimal() and text != '-42069':
                    return False

                if int(text) == -42069:
                    for macro in self.model.alwaysEvaluatedMacros:
                        ignored_nums.append(macro.macro_number)
                else:
                    for macro in self.model.numbersToPreppedDevices[int(text)].ignored_macros:
                        ignored_nums.append(macro.macro_number)

                if self._data[row][self.numind] not in ignored_nums:
                    return False
            else:
                if text not in str(self._data[row][col]).lower():
                    return False
        return True

    def middle_click_data(self, index: QModelIndex):
        """Method called by the ItemDelegate. Returns the data to be
        sent to the clipboard."""
        if index.column() == 0:
            return index.data()
        return self.channels[index.row()]


class MPSSortFilterModel(QSortFilterProxyModel):
    """Customized QSortFilterProxyModel to allow the user to sort and
    filter the customized QAbstractTableModel. Allows for functionality
    for the logic table, summary table, bypassed items table, and recent fault table"""
    def __init__(self, parent):
        super(MPSSortFilterModel, self).__init__(parent)
        self.filters = {}

    def setFilterByColumn(self, column: int, text: str):
        """Sets the filters to be used on individual columns."""
        self.filters[column] = text.lower()
        self.invalidateFilter()

    def removeFilterByColumn(self, column: int):
        """Removes the filters from a given column."""
        if column in self.filters:
            del self.filters[column]
            self.invalidateFilter()

    def lessThan(self, left: QModelIndex, right: QModelIndex):
        """Override QSortFilterProxyModel's lessThan method to sort
        columns to meet more personalized needs."""
        return self.sourceModel().less_than(left, right, self.sortOrder())

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        """Override QSortFilterProxyModel's filterAcceptsRow method to
        filter out rows based on the table's needs."""
        return self.sourceModel().filter_accepts_row(source_row, source_parent, self.filters)


class MPSItemDelegate(QStyledItemDelegate):
    """Customized QStyledItemDelegate to allow the user to copy
    some fault information from the table. Mimics functionality from
    PyDMWidgets."""
    def __init__(self, parent):
        super(MPSItemDelegate, self).__init__(parent)

    def editorEvent(self, event, model, option, index) -> bool:
        """Allow the user to copy a PV address by middle-clicking."""
        if (event.type() == QEvent.MouseButtonPress
                and event.button() == Qt.MiddleButton):
            clipboard = QApplication.clipboard()

            mode = clipboard.Clipboard
            if system() == 'Linux':
                mode = clipboard.Selection
            source_ind = model.mapToSource(index)
            text = model.sourceModel().middle_click_data(source_ind)
            clipboard.setText(text, mode=mode)

            new_event = QEvent(QEvent.Clipboard)
            QApplication.instance().sendEvent(clipboard, new_event)
            QToolTip.showText(event.globalPos(), text)
        return super().editorEvent(event, model, option, index)
