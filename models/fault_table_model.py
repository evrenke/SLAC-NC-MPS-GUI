from logging import getLogger
from qtpy.QtCore import (Qt, QModelIndex, QAbstractTableModel,
                         QSortFilterProxyModel)
from .enums import Statuses
from models.all_faults_model import ALLFaultsModel
from dbinteraction.configDB.link_node_fault import Link_Node_Fault as LNF
from dbinteraction.configDB.epics_fault import Epics_Fault as EF
from dbinteraction.configDB.link_node_channel_fault import Link_Node_Channel_Fault as LNCF


class FaultTableModel(QAbstractTableModel):
    """
    author: Evren Keskin
    ===================================================================
    This is a table model that holds the fault information for display.
    It is used as a connection between the UI display in fault_ui,
    and the models of retrieved data from ALLFaultsModel.
    It holds the rows of data that is used for table display in '_data'.
    For now, it is hard coded for LCLS use, but can easily be adapted for more flexibility
    ===================================================================

    The most important functions are
    __init__: used to create the table header, the hidden columns, and initialize what the user first sees
    set_data: used to set the table row data based on ALLFaultsModel info. This is what the user sees
    set_accepted: sets the shown column based on accepted checkboxes
    """
    logger = getLogger(__name__)

    def __init__(self, parent, fault_model: ALLFaultsModel):
        super(FaultTableModel, self).__init__(parent)
        self.fault_model = fault_model

        self.hdr_lst = (["Fault PV"])

        # Hidden column used for information about the data in the row
        self.hdr_lst += ["Fault Type", "Is Shown", "Fault Number"]

        self.type_ind = self.hdr_lst.index("Fault Type")
        self.shown_ind = self.hdr_lst.index("Is Shown")
        self.num_ind = self.hdr_lst.index("Fault Number")

        self.conind = [self.type_ind, self.shown_ind, self.num_ind]

        self.all_types = ['Epics Fault', 'Link Node Fault', 'Link Node Channel Fault', 'Link Processor Fault']
        self.accepted_types = ['Epics Fault', 'Link Node Fault', 'Link Node Channel Fault', 'Link Processor Fault']

        self._data = []  # table data, which will hold inputs from database data
        self.status = []

        self.set_data()

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
        # elif role == Qt.BackgroundRole:
        #     return Statuses.WHT.brush()
        elif role == Qt.ForegroundRole:
            return Qt.black

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: Qt.ItemDataRole):
        """Set the horizontal header's text."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.hdr_lst[section]

    def set_data(self):
        self._data = []
        self.status = []

        """Set initial data for each preppedFault.
        Populate each fault item with the PV, and fault type.
        Set the color to white (for disconnected).
        ???
        """
        for index, fault_num in enumerate(self.fault_model.nums_to_faults):
            lst = [self.fault_model.get_fault_by_num(fault_num).fault_name] * len(self.hdr_lst)
            lst[0] = self.fault_model.get_fault_by_num(fault_num).pv
            if self.fault_model.get_fault_by_num(fault_num).fault_type == EF:
                lst[1] = self.all_types[0]
            elif self.fault_model.get_fault_by_num(fault_num).fault_type == LNF:
                lst[1] = self.all_types[1]
            elif self.fault_model.get_fault_by_num(fault_num).fault_type == LNCF:
                lst[1] = self.all_types[2]
            else:  # self.fault_model.get_fault_by_num(fault).fault_type == LPF:
                lst[1] = self.all_types[3]

            if lst[1] in self.accepted_types:
                lst[2] = 'Y'
            else:
                lst[2] = 'N'

            lst[3] = fault_num

            self._data.append(lst)

            self.status.append(Statuses.WHT)

            self.dataChanged.emit(self.index(index, 0),
                                  self.index(index, 2))

    def set_accepted(self):
        """
        Set the acceptance of specific rows of data based on its type
        and the accepted types
        This will choose which rows are eventually hidden from the shown table
        """
        for row, lst in enumerate(self._data):
            if self._data[row][self.type_ind] in self.accepted_types and self._data[row][self.shown_ind] == 'N':
                self._data[row][self.shown_ind] = 'Y'
                self.dataChanged.emit(self.index(row, 0),
                                      self.index(row, 2))
            elif self._data[row][self.type_ind] not in self.accepted_types and self._data[row][self.shown_ind] == 'Y':
                self._data[row][self.shown_ind] = 'N'
                self.dataChanged.emit(self.index(row, 0),
                                      self.index(row, 2))

    def filter_accepts_row(self, row: int, parent: QModelIndex, filters: dict):
        """Called by MPSSortFilterProxyModel to filter out rows based on
        the table's needs."""
        for col, text in filters.items():
            if col == self.type_ind and text not in self.typesAccepted:
                return False
            if text not in str(self._data[row][col]).lower():
                return False
        return True


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

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        """Override QSortFilterProxyModel's filterAcceptsRow method to
        filter out rows based on the table's needs."""
        return self.sourceModel().filter_accepts_row(source_row, source_parent, self.filters)
