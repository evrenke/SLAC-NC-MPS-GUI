from functools import partial
from qtpy.QtCore import (Qt, Slot, QItemSelection)
from qtpy.QtWidgets import QHeaderView, QApplication
from models.fault_table_model import (FaultTableModel, MPSSortFilterModel)
from dbinteraction.configDB.link_node_fault import Link_Node_Fault as LNF
from dbinteraction.configDB.epics_fault import Epics_Fault as EF
from dbinteraction.configDB.link_node_channel_fault import Link_Node_Channel_Fault as LNCF
from dbinteraction.configDB.link_processor_fault import Link_Processor_Fault as LPF
from epics import caget
from mps_constants import (FAULT_STATE_POSTFIX, CHANNEL_PREFIX,
                           STATE_IS_OK_POSTFIX, BYPASS_VALUE_RVAL_POSTFIX, BYPASS_STRING_POSTFIX)


class FaultsUI:
    """
    author: Evren Keskin
    ===================================================================
    FaultUI is the class that connects the fault table model that
    tursn faults into a table in the UI
    It shows only the PV's and fault types to the user,
    but gives checkboxes for selection of types, and a search bar for fault PV's.
    ===================================================================
    """
    def fault_init(self):
        """
        Initializer for everything in Fault tab: Fault Table Model,
        Fault_Splitter, and the fault row count.
        """
        self.fault_tbl_model = FaultTableModel(self, self.model.configDB)

        self.fault_model = MPSSortFilterModel(self)
        self.fault_model.setSourceModel(self.fault_tbl_model)

        self.fault_model.setFilterByColumn(self.fault_tbl_model.shown_ind, 'Y')

        self.filters = []

        self.splitter_state = [1, 300]
        self.Fault_Splitter.setSizes([1, 0])
        self.Fault_Splitter.setCollapsible(0, False)
        self.Fault_Splitter.setStretchFactor(0, 1)

        self.fault_model.setFilterByColumn(0, "")

        self.fault_table_ui = self.ui.Faults_Table_View

        self.fault_table_ui.setModel(self.fault_model)
        self.fault_table_ui.sortByColumn(0, Qt.AscendingOrder)

        for i in range(self.fault_tbl_model.conind[1], self.fault_tbl_model.conind[-1] + 1):
            self.fault_table_ui.hideColumn(i)

        hdr = self.fault_table_ui.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)

        self.show_faults_row_count()

    def fault_connections(self):
        """Establish slot connections for the fault model and
        fault tab."""
        # Establish connections for faults checkboxes and text filter box
        self.ui.Epics_Faults_Checkbox.stateChanged.connect(self.show_epics_faults)
        self.ui.Link_Node_Faults_Checkbox.stateChanged.connect(self.show_link_node_faults)
        self.ui.Link_Node_Channel_Faults_Checkbox.stateChanged.connect(self.show_link_node_channel_faults)
        self.ui.Link_Processor_Faults_Checkbox.stateChanged.connect(self.show_link_processor_faults)

        self.ui.Fault_Filter_LineEdit.textChanged.connect(partial(self.fault_model.setFilterByColumn, 0))

        # Establish connections for showing the row count
        self.fault_model.rowsRemoved.connect(self.show_faults_row_count)
        self.fault_model.rowsInserted.connect(self.show_faults_row_count)
        self.fault_model.layoutChanged.connect(self.show_faults_row_count)

        # Establish connections for the selection details frame
        self.fault_table_ui.selectionModel().selectionChanged.connect(self.fault_selected)
        self.Fault_Selection_Close_Button.clicked.connect(self.details_closed)
        self.Fault_Splitter.splitterMoved.connect(self.save_fault_split_state)

    @Slot(int)
    def show_epics_faults(self, state):
        """Slot called when Inactive Checkbox is toggled. Determines if
        the inactive faults are shown. Only show faults that are active,
        this not including faults that could not establish a connection."""
        if not state:
            self.fault_tbl_model.accepted_types.remove(self.fault_tbl_model.all_types[0])
        else:
            self.fault_tbl_model.accepted_types.append(self.fault_tbl_model.all_types[0])

        self.fault_tbl_model.set_accepted()

    @Slot(int)
    def show_link_node_faults(self, state):
        """Slot called when Inactive Checkbox is toggled. Determines if
        the inactive faults are shown. Only show faults that are active,
        this not including faults that could not establish a connection."""
        if not state:
            self.fault_tbl_model.accepted_types.remove(self.fault_tbl_model.all_types[1])
        else:
            self.fault_tbl_model.accepted_types.append(self.fault_tbl_model.all_types[1])

        self.fault_tbl_model.set_accepted()

    @Slot(int)
    def show_link_node_channel_faults(self, state):
        """Slot called when Inactive Checkbox is toggled. Determines if
        the inactive faults are shown. Only show faults that are active,
        this not including faults that could not establish a connection."""
        if not state:
            self.fault_tbl_model.accepted_types.remove(self.fault_tbl_model.all_types[2])
        else:
            self.fault_tbl_model.accepted_types.append(self.fault_tbl_model.all_types[2])

        self.fault_tbl_model.set_accepted()

    @Slot(int)
    def show_link_processor_faults(self, state):
        """Slot called when Inactive Checkbox is toggled. Determines if
        the inactive faults are shown. Only show faults that are active,
        this not including faults that could not establish a connection."""
        if not state:
            self.fault_tbl_model.accepted_types.remove(self.fault_tbl_model.all_types[3])
        else:
            self.fault_tbl_model.accepted_types.append(self.fault_tbl_model.all_types[3])

        self.fault_tbl_model.set_accepted()

    @Slot()
    def show_faults_row_count(self):
        """When the number of displayed rows changes, update the row
        count at the bottom of the tab."""
        rows = self.fault_model.rowCount()
        self.ui.Fault_Number_Filters_Label.setText(f"Displaying {rows} / {len(self.model.configDB.nums_to_faults)} Faults")

    @Slot()
    def save_fault_split_state(self):
        """Saves the splitter size if both sections are not collapsed."""
        sizes = self.Fault_Splitter.sizes()
        if sizes[1]:
            self.splitter_state = sizes

    @Slot()
    def details_closed(self):
        """Slot to close the SelectionDetails widget."""
        self.fault_table_ui.clearSelection()
        self.Fault_Splitter.setSizes([1, 0])

    @Slot(QItemSelection, QItemSelection)
    def fault_selected(self, selected, deselected):
        """Slot called when a row is selected. This will change the
        SelectionDetailsUI widget and open it if it's hidden."""
        indexes = selected.indexes()
        if not indexes:
            indexes = deselected.indexes()
        row_ind = self.fault_model.mapToSource(indexes[0])

        # A hidden column holds the macro number for reference for the macros on the table
        # Its used here to easily get the macros
        fault_num = self.fault_tbl_model._data[row_ind.row()][self.fault_tbl_model.num_ind]
        fault = self.model.configDB.nums_to_faults[fault_num]
        self.set_fault_details(fault)

        # Show the selection details widget if its not there
        if not self.Fault_Splitter.sizes()[1]:
            self.Fault_Splitter.setSizes(self.splitter_state)

    def set_fault_details(self, fault):
        """
        Takes a given fault, and adjusts the UI for fault details with its information
        It also accounts for specific fault types, and hides unrelated rows of information
        """

        # Change the cursor to a waiting icon, sometimes PV connections can cause delays
        QApplication.setOverrideCursor(Qt.WaitCursor)

        ui = self.ui

        # For all common fault attributes
        ui.Fault_Area_Field.setText(fault.area)

        if fault.description is None or str.isspace(fault.description):
            ui.Fault_Description_Field.setText('-')  # this is to make sure that there is at least something shown
        else:
            ui.Fault_Description_Field.setText(fault.description)

        ui.Fault_PV_Field.setText(fault.pv)

        if fault.is_autorecoverable == 1:
            ui.Fault_Auto_Recoverable_Field.setText('Yes')
        else:
            ui.Fault_Auto_Recoverable_Field.setText('No')

        ui.Fault_Ok_State_Name_Field.setText(fault.ok_state_name)
        ui.Fault_Faulted_State_Name_Field.setText(fault.faulted_state_name)

        if fault.relatedPreppedMacro is not None:
            ui.Fault_Related_Macro_Field.setText(fault.relatedPreppedMacro.macro_name)
        else:
            ui.Fault_Related_Macro_Field.setText('None')
        # Current state fields require PV usage
        ui.Fault_Current_State_Field.setText(caget(fault.pv + FAULT_STATE_POSTFIX, as_string=True))
        ui.Fault_Current_State_Byte_Indicator.channel = CHANNEL_PREFIX + fault.pv + STATE_IS_OK_POSTFIX

        # For epics fault specific attributes
        if fault.fault_type == EF:
            ui.Fault_Input_PV_Label.show()
            ui.Fault_Input_PV_Field.show()
            ui.Fault_Input_PV_Field.setText(fault.input_pv)
        else:
            ui.Fault_Input_PV_Label.hide()
            ui.Fault_Input_PV_Field.hide()

        # For link node fault specific attributes

        if fault.fault_type == LNF:
            ui.Fault_Hostname_Label.show()
            ui.Fault_Hostname_Field.show()
            ui.Fault_Hostname_Field.setText(fault.hostname)
        else:
            ui.Fault_Hostname_Label.hide()
            ui.Fault_Hostname_Field.hide()

        # For link node fault and link node channel fault specific attributes
        if fault.fault_type == LNF or fault.fault_type == LNCF:
            ui.Fault_Link_Node_ID_Label.show()
            ui.Fault_Link_Node_ID_Field.show()
            ui.Fault_Link_Node_ID_Field.setText(str(fault.link_node_id))
        else:
            ui.Fault_Link_Node_ID_Label.hide()
            ui.Fault_Link_Node_ID_Field.hide()

        if fault.fault_type == LNCF:
            ui.Fault_Card_Label.show()
            ui.Fault_Card_Field.show()
            ui.Fault_Channel_Label.show()
            ui.Fault_Channel_Field.show()
            ui.Fault_Deadman_Label.show()
            ui.Fault_Deadman_Field.show()

            ui.Fault_Card_Field.setText(str(fault.card))
            ui.Fault_Channel_Field.setText(str(fault.channel))
            if fault.is_deadman:
                ui.Fault_Deadman_Field.setText('Yes')
            else:
                ui.Fault_Deadman_Field.setText('No')
        else:
            ui.Fault_Card_Label.hide()
            ui.Fault_Card_Field.hide()
            ui.Fault_Channel_Label.hide()
            ui.Fault_Channel_Field.hide()
            ui.Fault_Deadman_Label.hide()
            ui.Fault_Deadman_Field.hide()

        # For epics fault, link node channel fault, and link processor fault position attributes

        if fault.fault_type == EF or fault.fault_type == LNCF or fault.fault_type == LPF:
            ui.Fault_Position_Label.show()
            ui.Fault_Position_Field.show()
            ui.Fault_Position_Field.setText(f'({fault.position_x}, {fault.position_y}, {fault.position_z})')

            if caget(fault.pv + BYPASS_VALUE_RVAL_POSTFIX):
                ui.Fault_Bypassed_Label.show()
            else:
                ui.Fault_Bypassed_Label.hide()
        else:
            ui.Fault_Position_Label.hide()
            ui.Fault_Position_Field.hide()

            if caget(fault.pv + BYPASS_STRING_POSTFIX) != 0:
                ui.Fault_Bypassed_Label.show()
            else:
                ui.Fault_Bypassed_Label.hide()

        QApplication.restoreOverrideCursor()
