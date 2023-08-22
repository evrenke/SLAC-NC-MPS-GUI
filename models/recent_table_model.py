from logging import getLogger
from platform import system
from qtpy.QtCore import (Qt, QModelIndex, QAbstractTableModel,
                         QEvent, QSortFilterProxyModel)
from qtpy.QtWidgets import (QStyledItemDelegate, QApplication, QToolTip)
from .enums import Statuses
from models.all_logic_model import AllLogicModel
from models.prepped_macro_state import PreppedMacroState
import json
import fcntl
import time
from mps_constants import RECENT_FAULTS_MAX


class RecentTableModel(QAbstractTableModel):
    """
    author: Evren Keskin
    ===================================================================
    This is a table model about the recent states of macros.
    It shows a date of a latest state change, along with the macro and what that state is.
    It is only as accurate as the current state PV is accurate.
    The recent states are grabbed by reading a JSON file which is written to by a daemon.
    The JSON represents a recent state by date, macro number, and state number.
    This table reconstructs that into the full information the user needs to see.
    The daemon and this program regularly exchange locks on this file
    this for reading, and the daemon for writing.
    This is mainly so that the JSON will be up to date without the GUI.
    ===================================================================
    """
    logger = getLogger(__name__)

    def __init__(self, parent, model: AllLogicModel, rates_list):
        super(RecentTableModel, self).__init__(parent)
        self.model = model

        self.hdr_lst = (["Date", "Name", "State", "Min"])

        self.hdr_lst += rates_list

        # table data, which will hold inputs from database data
        self._data = [['not an item', 'DATABASE ERROR', 'no state', '--',
                       '--', '--', '--', '--', '--', '--', '--', '--']] * RECENT_FAULTS_MAX
        self.channels = []  # channels used to copy the name of the logic item easily with middle click

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
        elif role == Qt.BackgroundRole and 1 < index.column():
            return Statuses.BGD.brush()
        elif role == Qt.ForegroundRole:
            col = index.column()
            txt = index.data()

            if (2 < col) and (txt == '0 Hz' or txt == 'Invalid' or txt == 'Unknown'):
                return Statuses.RED.brush()

            elif (2 < col) and (txt == '1 Hz' or txt == '10 Hz' or txt == '30 Hz' or txt == '60 Hz'):
                if self.model.linactype == 'LCLS':
                    return Statuses.YEL.brush()
                elif txt == '30 Hz':  # FACET
                    return Statuses.GRN.brush()
                return Statuses.YEL.brush()

            elif (2 < col) and (txt == '120 Hz'
                                or txt == 'Single Shot'
                                or txt == 'Burst Mode'
                                or txt == '--'):
                return Statuses.GRN.brush()

            elif col != 0 and col != 1:  # catch all that makes all non-name remainders white
                return Statuses.GRN.brush()

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: Qt.ItemDataRole):
        """Set the horizontal header's text."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.hdr_lst[section]

    def set_data(self, jsonFilePath):
        """
        Set initial data for each row, based on a recent state.
        Populate each recent fault item with the
        date, macro name, state name, and state rates info.
        """
        time.sleep(0.1)  # Give the daemon additional time to go first
        state_messages = self.get_recent_states(jsonFilePath)

        self._data = []

        self.channels = []

        for index, recent_state in enumerate(state_messages):
            macro_name = recent_state['macro']
            state_name = recent_state['statename']
            state_rates = recent_state['staterates']
            date = recent_state['date']

            lst = [date] * len(self.hdr_lst)
            lst[0] = date
            lst[1] = macro_name
            lst[2] = state_name
            for index, rate in enumerate(state_rates):
                lst[index + 3] = rate

            self._data.insert(0, lst)

            self.dataChanged.emit(self.index(index, 0),
                                  self.index(index, 10))

            self.channels.append(macro_name)

    def get_recent_states(self, jsonFilepath):

        file_path = jsonFilepath
        file_lock = open(file_path, 'a')  # Open the file
        recent_states_list = []

        # Lock the file (fcntl.F_LOCK)
        try:
            fcntl.flock(file_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            # print("File is locked")

            input_file = open(jsonFilepath)
            json_array = json.load(input_file)
            recent_states_list = []

            for item in json_array['recent faults']:
                recent_state_details = {'statename': None, 'staterates': None, 'macro': None, 'date': None}
                recent_state_details['statename'] = item['statename']
                recent_state_details['staterates'] = item['staterates']
                recent_state_details['macro'] = item['macro']
                recent_state_details['date'] = item['date']
                recent_states_list.append(recent_state_details)

        except IOError:
            # print("File is already locked by another process")
            time.sleep(2)
            return self.get_recent_states(jsonFilepath)

        finally:
            # Unlock the file (fcntl.F_UNLOCK)
            fcntl.flock(file_lock.fileno(), fcntl.LOCK_UN)
            # print("File is unlocked")
            file_lock.close()

        return recent_states_list

    def less_than(self, left: QModelIndex, right: QModelIndex, sortorder: Qt.SortOrder):
        """Called by MPSSortFilterProxyModel to sort rows based on the
        app's status."""
        left_state = left.data()
        right_state = right.data()

        # never sorted, this is unused

        if left.column() > 2:
            return PreppedMacroState.get_val_to_enum(left_state) < PreppedMacroState.get_val_to_enum(right_state)

        return left_state < right_state

    def filter_accepts_row(self, row: int, parent: QModelIndex, filters: dict):
        """
        Called by MPSSortFilterProxyModel to filter out rows based on
        the table's needs.
        """
        for col, text in filters.items():
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
