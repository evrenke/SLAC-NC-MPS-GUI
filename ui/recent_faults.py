from qtpy.QtCore import (Slot, QPoint)
from qtpy.QtWidgets import (QHeaderView, QAction, QMenu, QTableView)
from models.recent_table_model import RecentTableModel, MPSSortFilterModel, MPSItemDelegate
from functools import partial
from epics import PV
from mps_constants import CURRENT_STATES_POSTFIX, RECENT_FAULTS_MAX


class RecentFaultsUI():
    """
    author: Evren Keskin
    ===================================================================
    RecentFaultsUI is the class that connects the recent states model
    into the recent faults table view in UI.
    It shows a list of all fault/state changes read from a JSON file.
    These can be filtered, and are updating frequently based on current state
    PV changed.
    ===================================================================
    """
    def recent_faults_init(self, is_cud, rates_list, accel_type):
        """
        Initializer for everything in Logic tab: Message Table Model,
        Message Item Delegate, and the header.
        """
        self.recent_states_tbl_model = RecentTableModel(self, self.model, rates_list,
                                                        self.recentStatesDBPath, accel_type)

        self.recent_faults_model = MPSSortFilterModel(self)
        self.recent_faults_model.setSourceModel(self.recent_states_tbl_model)

        recentFaultsTable = self.ui.Recent_Faults_View
        recentFaultsTable.setModel(self.recent_faults_model)
        recentFaultsTable.hideColumn(self.recent_states_tbl_model.numind)

        self.recent_delegate = MPSItemDelegate(self)
        recentFaultsTable.setItemDelegate(self.recent_delegate)

        hdr = recentFaultsTable.horizontalHeader()
        recentFaultsTable.setColumnWidth(3, 85)
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)

        if not is_cud:
            self.show_recent_faults_row_count()
            # Initialize connecting state records of macros to the macros in logic tab
            self.selected_num = None
            self.recent_action = QAction("Open it in Logic tab", self)
            self.recent_menu = QMenu(self)
            self.recent_menu.addAction(self.recent_action)
        else:
            hdr.resizeSection(0, 245)
            hdr.resizeSection(1, 360)
            hdr.resizeSection(2, 180)

    def recent_faults_connections(self, IOC_PREFIX, is_cud):
        """
        Establish PV and slot connections for the recent faults model tab
        Archive connections allows for the table to update with current state accuracy
        """

        if not is_cud:
            # Start a PV cchannel to check for JSON file changes
            # A daemon process in another parallel program will update the JSON file with PV changes
            self.recentFaultsUpdatePV = PV(IOC_PREFIX + CURRENT_STATES_POSTFIX, callback=self.update_table)
            # Establish connections for showing the row count
            self.recent_faults_model.rowsRemoved.connect(self.show_recent_faults_row_count)
            self.recent_faults_model.rowsInserted.connect(self.show_recent_faults_row_count)
            self.recent_faults_model.layoutChanged.connect(self.show_recent_faults_row_count)
            # Establish connection for the name text search filtering
            self.ui.Recent_Fault_Search_Line_Edit.textChanged.connect(
                partial(self.filter_recent_faults))
            # Establish connections for the context menu and its action.
            self.ui.Recent_Faults_View.customContextMenuRequested.connect(
                self.recent_fault_custom_context_menu)
            self.recent_action.triggered.connect(self.recent_fault_select)
        else:
            # Start a PV cchannel to check for JSON file changes
            # A daemon process in another parallel program will update the JSON file with PV changes
            self.recentFaultsUpdatePV = PV(IOC_PREFIX + CURRENT_STATES_POSTFIX, callback=self.update_table_cud)

    @Slot()
    def filter_recent_faults(self, text):
        self.recent_faults_model.setFilterByColumn(1, text)

    @Slot()
    def update_table(self, **kw):
        """
        Use the sqlite db file path that the UI was launched with to update the table data
        """
        self.recent_states_tbl_model.set_data()
        self.show_recent_faults_row_count()

    @Slot()
    def update_table_cud(self, **kw):
        """
        Use the sqlite db file path that the UI was launched with to update the table data
        """
        self.recent_states_tbl_model.set_data()

    @Slot()
    def show_recent_faults_row_count(self):
        """
        When the number of displayed rows changes, update the row
        count at the bottom of the tab.
        """
        rows = self.recent_faults_model.rowCount()
        self.ui.Recent_Faults_Number_Filters_Label.setText(f"Displaying {rows} / {RECENT_FAULTS_MAX} Recent Faults")

    @Slot(QPoint)
    def recent_fault_custom_context_menu(self, pos: QPoint):
        """
        Create a custom context menu to open the Macro's Details.
        """
        table = self.sender()
        if not table or not isinstance(table, QTableView):
            self.logger.error("Internal error: "
                              f"{type(table)} is not a QTableView")
            return
        index = table.indexAt(pos)

        if index.isValid():
            self.selected_num = self.ui.Recent_Faults_View.model().index(index.row(),
                                                                         self.recent_states_tbl_model.numind).data()
            self.recent_menu.popup(table.viewport().mapToGlobal(pos))

    def recent_fault_select(self):
        """
        Set the selected fault in the Logic Tab to open the
        SelectionDetails widget. Then change tabs to the Logic Tab.
        """

        for row in range(0, len(self.logic_model.sourceModel()._data)):
            searched_index = self.logic_model.sourceModel().index(row, self.recent_states_tbl_model.numind)
            name_index = self.logic_model.sourceModel().index(row, 0)
            if self.selected_num == (searched_index.data()):
                self.ui.Logic_Search_Line_Edit.setText("")
                index = self.logic_model.mapFromSource(name_index)
                self.ui.Logic_Table_View.setCurrentIndex(index)
                self.ui.Logic_Table_View.scrollTo(index)
                self.ui.Main_Tab_Widget.setCurrentIndex(2)
                return
