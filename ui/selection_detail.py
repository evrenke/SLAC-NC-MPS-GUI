from json import dumps
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (QHeaderView, QTableWidgetItem)
from qtpy.QtGui import QColor
from pydm.widgets import PyDMShellCommand
from models.prepped_macro_state import PreppedMacroState
import math
from dbinteraction.configDB.link_node_fault import Link_Node_Fault as LNF
from dbinteraction.configDB.epics_fault import Epics_Fault as EF
from dbinteraction.configDB.link_node_channel_fault import Link_Node_Channel_Fault as LNCF
from dbinteraction.configDB.link_processor_fault import Link_Processor_Fault as LPF
from os import path
from mps_constants import FAULT_STATE_CURRENT_POSTFIX, FAULT_STATE_POSTFIX


class SelectionDetailsHelper:
    """
    author: Evren Keskin
    ============================================================================================
    SelectionDetailsUI is a class that
    attaches logic table's selection to the selection detail panel.
    The selection of an item fills a truth table with related state information.
    The selection panel also fills out information on the fault PV's of the selected device.
    It also attaches buttons for each PV, and attaches the bypass window button.

    It works in parallel with LogicUI and IgnoreUI
    to make the Logic and Ignore tabs of the main application work.
    ============================================================================================
    """
    def __init__(self, rates_list, mpslogicmodel, tab_splitter, table_view, close_button, name_label, ignore_label,
                 current_state_label, code_label, code_section_label, bypass_button, truth_table,
                 pvs_table, logic_model, logic_tbl_model, IOC_PREFIX):
        # default_dtl_hdr holds the permanent columns of the table
        # without the addition of truth table values
        self.default_dtl_hdr = ["State", "Min Rate"]
        self.default_dtl_hdr += rates_list

        self.dtl_hdr = self.default_dtl_hdr.copy()

        self.mpslogicmodel = mpslogicmodel
        self.tab_splitter = tab_splitter
        self.table_view = table_view
        self.close_button = close_button
        self.name_label = name_label
        self.ignore_label = ignore_label
        self.current_state_label = current_state_label
        self.code_label = code_label
        self.code_section_label = code_section_label
        self.bypass_button = bypass_button
        self.truth_table = truth_table
        self.pvs_table = pvs_table
        self.logic_model = logic_model
        self.logic_tbl_model = logic_tbl_model
        self.IOC_PREFIX = IOC_PREFIX

        tt_hdr = self.truth_table.horizontalHeader()
        tt_hdr.setSectionResizeMode(QHeaderView.Stretch)

        bold_font = tt_hdr.font()
        bold_font.setBold(True)
        tt_hdr.setFont(bold_font)

        self.pvs_hdr_columns = ["", "Current PV", "Latched PV", "Related Information"]
        self.pvs_table.setColumnCount(len(self.pvs_hdr_columns))
        self.pvs_table.setHorizontalHeaderLabels(self.pvs_hdr_columns)

        pvs_hdr = self.pvs_table.horizontalHeader()
        pvs_hdr.setSectionResizeMode(QHeaderView.Stretch)

        bold_font2 = pvs_hdr.font()
        bold_font2.setBold(True)
        pvs_hdr.setFont(bold_font2)

        self.splitter_state = [1, 400]
        self.tab_splitter.setSizes([1, 0])
        self.tab_splitter.setCollapsible(0, False)
        self.tab_splitter.setStretchFactor(0, 1)

    def selection_connections(self):
        """Set up slot connections for the Selection Details section."""
        # Establish connections for the SelectionDetails widget
        self.table_view.selectionModel().selectionChanged.connect(self.selected)
        self.close_button.clicked.connect(self.details_closed)
        self.tab_splitter.splitterMoved.connect(self.save_split_state)

    def set_states_details(self, macro):
        """Get the macro and inputs. Set necessary labels in
        the Selection Details section."""
        self.name_label.setText(macro.macro_name)

        # Set text for the ignore conditions for this macro device
        ign_str = ", ".join([ign for ign in self.mpslogicmodel.get_ignoring_macro_names(macro.macro_name)])
        self.ignore_label.setText(ign_str if ign_str else "--")

        # Set text for the name of the current state of this macro
        current_state_name = macro.get_current_state().state_name
        if current_state_name:
            self.current_state_label.setText(current_state_name)
        else:
            self.current_state_label.setText('--')

        # Check if the selected macro is code or not, and either remove the code row, or
        # Set text for the code obtained for this macro
        if macro.is_code:
            """make code data appear"""
            self.code_label.setVisible(True)
            self.code_section_label.setVisible(True)
            self.code_label.setText(macro.code)
        else:
            """make code data disappear"""
            self.code_label.setVisible(False)
            self.code_section_label.setVisible(False)
            self.code_label.setText('--')

        # Set the bypass button to launch a new window for the bypass screen
        # Feed it all of the relevant information about the selected device
        self.bypass_button.macros = dumps({'DEVICE_NAME': macro.macro_name,
                                           'DEVICE_CURRENT_STATE_NUMBER':
                                           int(macro.get_current_state().state_number),
                                           'DEVICE_FAULT_PVS': [fault.pv for fault in macro.faults],
                                           'DEVICE_FAULT_NUMBERS': [fault.fault_number for fault in macro.faults],
                                           'DEVICE_MACRO_STATES':
                                           [state.state_name for state in macro.macro_states],
                                           'DEVICE_MACRO_STATE_MINS':
                                           [PreppedMacroState.get_enum_to_val(state.get_min_rate()) for state in
                                            macro.macro_states],
                                           'DEVICE_OK_STATES': [fault.ok_state_name for fault in macro.faults],
                                           'DEVICE_FAULTED_STATES':
                                           [fault.faulted_state_name for fault in macro.faults],
                                           'DEVICE_IS_CODE': macro.is_code,
                                           'IOC_PREFIX': self.IOC_PREFIX})

        self.pop_truth_table(macro)

        self.pop_pv_table(macro)

    def clear_table(self, table, row_count, col_count):
        """Clear the contents of the Truth Table or PV Table."""
        table.clearContents()
        table.setRowCount(row_count)
        for i in range(row_count):
            for j in range(col_count):
                table.setItem(i, j, CellItem("--"))

    def pop_truth_table(self, macro):
        """
        Populate the states truth_table.
        The number of truth states is based on the base 2 log of device states.
        The states table shows all possible states of the device,
        with the corrolating truth values shown.
        """
        cols = len(self.dtl_hdr)
        self.clear_table(self.truth_table, len(macro.macro_states), cols)

        # 1) Check how many truth states to add as columns. (code macros have none)
        self.dtl_hdr = self.default_dtl_hdr.copy()
        if macro.is_code != 1:
            self.code_section_label.height = 0
            self.code_label.height = 0
            for columnIndex in range(0, int(math.log2(len(macro.macro_states)))):
                self.dtl_hdr.insert(1 + columnIndex,
                                    chr(65 + int(math.log2(len(macro.macro_states))) - columnIndex - 1))

        # 2) Adjust table to the right number of columns
        self.truth_table.setColumnCount(len(self.dtl_hdr))
        self.truth_table.setHorizontalHeaderLabels(self.dtl_hdr)

        # 3) For each macro state, add its information to the table
        # And if its not a code macro, add its truth table logic values
        for i, state in enumerate(macro.macro_states):
            # Each state needs to show its name, what truth table values activate it
            # And then the rates related with that state
            name_item = CellItem(state.state_name)
            self.truth_table.setItem(i, 0, name_item)
            truth_table_columns = 0
            if not macro.is_code:
                for columnIndex in range(0, int(math.log2(len(macro.macro_states)))):
                    logic_str = self.get_truth_table_logic(i, int(math.log2(len(macro.macro_states))) - columnIndex - 1)
                    logic_item = CellItem(logic_str)
                    self.truth_table.setItem(i, columnIndex + 1, logic_item)
                    truth_table_columns += 1

            min_rate_item = CellItem(PreppedMacroState.get_enum_to_val(state.get_min_rate()))
            self.truth_table.setItem(i, 1 + truth_table_columns, min_rate_item)
            for col_index in range(2, len(self.dtl_hdr) - truth_table_columns):
                rate_item = CellItem(PreppedMacroState.get_enum_to_val(state.rate_enums[col_index - 2]))
                self.truth_table.setItem(i, col_index + truth_table_columns, rate_item)

            # Give a highlight color to the current state of the macro
            if i == macro.current_index and not macro.has_special_error_state:
                for col in range(0, len(self.dtl_hdr)):
                    self.truth_table.item(i, col).setBackground(QColor(27, 120, 178))

    def get_truth_table_logic(self, rowIndex: int, columnIndex: int):
        """
        Gets the truth table logic for any given row and column
        """
        if 2.0 > ((rowIndex) / (2 ** (columnIndex))) % 2 >= 1.0:
            return "T"
        return "F"

    def pop_pv_table(self, macro):
        """
        Display all PVs used by macro devices.
        Rightmost column is a button to open the edm
        associated with the fault.
        """
        self.clear_table(self.pvs_table, len(macro.faults), 4)
        for i, fault in enumerate(macro.faults):
            item0 = CellItem(chr(65 + i))
            item1 = CellItem(fault.pv + FAULT_STATE_CURRENT_POSTFIX)
            item2 = CellItem(fault.pv + FAULT_STATE_POSTFIX)
            item3 = self.get_EDM_button(fault)
            self.pvs_table.setItem(i, 0, item0)
            self.pvs_table.setItem(i, 1, item1)
            self.pvs_table.setItem(i, 2, item2)
            self.pvs_table.setCellWidget(i, 3, item3)

    def get_EDM_button(self, fault):
        """
        Creates a PyDMShellCommand button
        for connecting to a separate EDM screen based on fault type
        """
        edmcommand = self.get_edm_command(fault)
        buttontext = 'My cool button'
        if fault.fault_type is EF:
            buttontext = 'EPICS Fault PV...'
        elif fault.fault_type is LNF:
            buttontext = 'Link Node Fault PV...'
        elif fault.fault_type is LNCF:
            buttontext = 'Link Node Channel Fault...'
        elif fault.fault_type is LPF:
            buttontext = 'Link Processor Fault...'

        edmbutton = PyDMShellCommand(command=edmcommand, title=buttontext)
        edmbutton.setText(buttontext)
        return edmbutton

    def get_edm_command(self, fault):
        """
        Gets the command used for launching fault EDM screens
        """
        edmCommand = ""
        TOOLS = path.expandvars("$TOOLS")

        if fault.fault_type is EF:
            edmCommand = "edm -x "+TOOLS+"/edm/display/mps/EPICSFaultInputs.edl"
        elif fault.fault_type is LNF:
            edmCommand = f'edm -x ${TOOLS}/edm/display/mps/LinkNodeAll.edl'
        elif fault.fault_type is LNCF:
            LNid = fault.link_node_id
            edmCommand = "edm -x "+TOOLS+"/edm/display/mps/LinkNode"+str(LNid)+".edl"
        elif fault.fault_type is LPF:
            edmCommand = "edm -x "+TOOLS+"/edm/display/mps/LPFaultInputs.edl"
        else:
            edmCommand = None  # SHOULD NOT HAPPEN, but here just in case

        return edmCommand

    # @Slot()
    def save_split_state(self):
        """Saves the splitter size if both sections are not collapsed."""
        sizes = self.tab_splitter.sizes()
        if sizes[1]:
            self.splitter_state = sizes

    # @Slot(QItemSelection, QItemSelection)
    def selected(self, selected, deselected):
        """Slot called when a row is selected. This will change the
        SelectionDetailsUI widget and open it if it's hidden."""
        indexes = selected.indexes()
        if not indexes:
            indexes = deselected.indexes()
        row_ind = self.logic_model.mapToSource(indexes[0])

        # A hidden column holds the macro number for reference for the macros on the table
        # Its used here to easily get the macros
        macro_num = self.logic_tbl_model._data[row_ind.row()][self.logic_tbl_model.numind]
        macro = self.mpslogicmodel.numbersToPreppedDevices[macro_num]
        self.set_states_details(macro)

        # Show the selection details widget if its not there
        if not self.tab_splitter.sizes()[1]:
            self.tab_splitter.setSizes(self.splitter_state)

    # @Slot()
    def details_closed(self):
        """Slot to close the SelectionDetails widget."""
        self.table_view.clearSelection()
        self.tab_splitter.setSizes([1, 0])


class CellItem(QTableWidgetItem):
    """Personalized QTableWidgetItem that sets preferred settings."""
    def __init__(self, text: str, *args, **kwargs):
        super(CellItem, self).__init__(text, *args, **kwargs)
        self.setTextAlignment(Qt.AlignCenter)
        self.setBackground(Qt.white)
