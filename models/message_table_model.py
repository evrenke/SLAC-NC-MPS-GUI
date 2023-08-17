from logging import getLogger
from qtpy.QtCore import (Qt, QModelIndex, QAbstractTableModel,
                         QSortFilterProxyModel)
from .enums import Statuses
from models.all_messages_model import AllMessagesModel
from datetime import datetime
from mps_constants import FROM_1970_TO_1990_IN_SECONDS


class MessageTableModel(QAbstractTableModel):
    """
    author: Evren Keskin
    ===================================================================
    This is a table model that holds the message information for display.
    It is used as a connection between the UI display in history_ui,
    and the models of retrieved data from AllMessagesModel.
    It holds the rows of data that is used for table display in '_data'.
    For now, it is hard coded for LCLS use
    but can easily be adapted for more flexibility
    ===================================================================

    The most important functions are
    __init__: used to create the table header, the hidden columns
    and initialize what the user first sees.
    set_data: used to set the table row data based on MPSFaultModel info.
    This is what the user sees
    set_accepted: sets the shown column based on accepted checkboxes
    """
    logger = getLogger(__name__)

    def __init__(self, parent, messages_model: AllMessagesModel):
        super(MessageTableModel, self).__init__(parent)
        self.message_model = messages_model

        self.hdr_lst = (["Date", "Message"])

        self._data = []  # table data, which will hold inputs from database
        self.status = []
        self.filteringThatOneMessage = False

    def rowCount(self, index: QModelIndex = QModelIndex()):
        """Return the number of rows in the model."""
        return 0 if index.isValid() else len(self._data)

    def columnCount(self, index: QModelIndex = QModelIndex()):
        """Return the number of columns in the model."""
        return len(self.hdr_lst)

    def insertRows(self, new_row, position, rows, parent=QModelIndex()):
        """
        Insert a new message row at the top or bottom based on position negativity
        Negative inserts are from the top, and positives are from the bottom
        """
        if position >= 0:
            self.beginInsertRows(parent, 0, 0)
            self._data.insert(position, new_row)
            self.endInsertRows()
        else:
            self.beginInsertRows(parent, 0, 0)
            self._data.append(new_row)
            self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent=QModelIndex()):
        start, end = position, rows
        self.beginRemoveRows(parent, start, end)
        del self._data[start:end + 1]
        self.endRemoveRows()
        return True

    def data(self, index: QModelIndex, role: Qt.ItemDataRole):
        """Return the index's text, alignment, background color,
        OR foreground color."""
        if not index.isValid():
            return
        elif role == Qt.DisplayRole:
            return str(self._data[index.row()][index.column()])
        elif role == Qt.TextAlignmentRole and 0 < index.column():
            return Qt.AlignCenter
        # elif role == Qt.BackgroundRole:
        #     return Statuses.WHT.brush()
        elif role == Qt.ForegroundRole:
            row = index.row()
            col = index.column()
            if col != 0:
                return self.status[row].brush()
            return Qt.black

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: Qt.ItemDataRole):
        """Set the horizontal header's text."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.hdr_lst[section]

    def initialize_live(self):
        self.lastLiveIndex = 0
        liveMessages = self.message_model.liveMessages
        for index, messageObj in enumerate(liveMessages):
            lst = [messageObj.message] * len(self.hdr_lst)
            lst[0] = datetime.fromtimestamp(messageObj.seconds_from_1990
                                            + FROM_1970_TO_1990_IN_SECONDS)
            lst[1] = messageObj.message

            self.status.append(self.get_status_from_type(messageObj.message_type))

            self.insertRows(lst, self.lastLiveIndex, 1)
            self.lastLiveIndex += 1

    def update_live(self):
        self.message_model.update_live_messages()
        liveMessages = self.message_model.liveMessages[self.lastLiveIndex:]
        for index, messageObj in enumerate(liveMessages):
            lst = [messageObj.message] * len(self.hdr_lst)
            lst[0] = datetime.fromtimestamp(messageObj.seconds_from_1990
                                            + FROM_1970_TO_1990_IN_SECONDS)
            lst[1] = messageObj.message

            self.status.append(self.get_status_from_type(messageObj.message_type))

            self.insertRows(lst, index, 1)
            self.lastLiveIndex += 1

    def update_interactive(self, start, end):
        self.removeRows(0, self.rowCount())

        self.message_model.update_interval_messages(start, end)

        interactiveMessages = self.message_model.interactiveMessages
        for index, messageObj in enumerate(interactiveMessages):
            lst = [messageObj.message] * len(self.hdr_lst)
            lst[0] = datetime.fromtimestamp(messageObj.seconds_from_1990
                                            + FROM_1970_TO_1990_IN_SECONDS)
            lst[1] = messageObj.message

            self.status.append(self.get_status_from_type(messageObj.message_type))

            self.insertRows(lst, -1, 1)

    def get_status_from_type(self, message_type):
        status = Statuses.BGD
        if message_type == 'BD':
            status = Statuses.CYN  # here for comedic effect, this type of message is unused since 2009
        elif message_type == 'BR':
            status = Statuses.BLU
        elif message_type == 'BT':
            status = Statuses.YEL
        elif message_type == 'BV':
            status = Statuses.MAG
        else:  # if messageObj.message_type == 'F':
            status = Statuses.BGD
        return status

    def filter_accepts_row(self, row: int, parent: QModelIndex, filters: dict):
        """Called by MPSSortFilterProxyModel to filter out rows based on
        the table's needs."""
        for col, text in filters.items():
            if text not in str(self._data[row][col]).lower():
                return False
        return True


class MPSSortFilterModel(QSortFilterProxyModel):
    """Customized QSortFilterProxyModel to allow the user to sort and
    filter the customized QAbstractTableModel. Allows for functionality
    for the logic table, summary table,
    bypassed items table, and recent fault table"""
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

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        """Override QSortFilterProxyModel's filterAcceptsRow method to
        filter out rows based on the table's needs."""
        return self.sourceModel().filter_accepts_row(source_row,
                                                     source_parent,
                                                     self.filters)
