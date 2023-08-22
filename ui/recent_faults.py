from qtpy.QtCore import Slot
from qtpy.QtWidgets import QHeaderView
from models.recent_table_model import RecentTableModel
from models.recent_table_model import MPSSortFilterModel
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
    def recent_faults_init(self, is_cud, rates_list):
        """
        Initializer for everything in Logic tab: Message Table Model,
        Message Item Delegate, and the header.
        """
        self.recent_states_tbl_model = RecentTableModel(self, self.model, rates_list)

        self.recent_faults_model = MPSSortFilterModel(self)
        self.recent_faults_model.setSourceModel(self.recent_states_tbl_model)

        recentFaultsTable = self.ui.Recent_Faults_View
        recentFaultsTable.setModel(self.recent_faults_model)

        hdr = recentFaultsTable.horizontalHeader()
        recentFaultsTable.setColumnWidth(3, 85)
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)

        if not is_cud:
            self.show_recent_faults_row_count()
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
        Use the json file path that the UI was launched with to update the table data
        """
        self.recent_states_tbl_model.set_data(self.jsonFilePath)
        self.show_recent_faults_row_count()

    @Slot()
    def update_table_cud(self, **kw):
        """
        Use the json file path that the UI was launched with to update the table data
        """
        self.recent_states_tbl_model.set_data(self.jsonFilePath)

    @Slot()
    def show_recent_faults_row_count(self):
        """
        When the number of displayed rows changes, update the row
        count at the bottom of the tab.
        """
        rows = self.recent_faults_model.rowCount()
        self.ui.Recent_Faults_Number_Filters_Label.setText(f"Displaying {rows} / {RECENT_FAULTS_MAX} Recent Faults")
