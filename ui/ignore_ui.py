from qtpy.QtCore import (Qt, Slot, QItemSelection)
from qtpy.QtWidgets import QHeaderView
from models.logic_table_model import MPSSortFilterModel
from ui.selection_detail import SelectionDetailsHelper


class IgnoreUI():
    """
    author: Evren Keskin
    ===================================================================
    IgnoreUI is the class that connects the logic table model
    into two filtered table views.
    The left table, IgnoringLogicTable, holds the conditions of ignoring macros
    The right table, IgnoredLogicTable, holds the macros that any selected condition macro ignores
    Selection from the left populates the right
    Additionally, a special selection of 'Always Evaluated' exists,
    to allow choosing never ignored macros in one list
    ===================================================================
    """
    def ignore_init(self, rates_list, IOC_PREFIX):
        """
        Initializer for everything in Ignore tab: Ignore Logic Table Model,
        Ignore Macro Table Model, Selection Screen, Item Delegate, and the headers.
        """

        # The Left table of Ignoring Macros
        self.ignoring_model = MPSSortFilterModel(self)
        self.ignoring_model.setSourceModel(self.logic_tbl_model)

        self.ignoring_model.setFilterByColumn(self.logic_tbl_model.cind, 'Y')
        self.ui.Ignoring_Logic_Table.setModel(self.ignoring_model)
        for i in range(1, self.logic_tbl_model.conind[-1] + 1):
            self.ui.Ignoring_Logic_Table.hideColumn(i)
        self.ui.Ignoring_Logic_Table.showColumn(self.logic_tbl_model.mmrind)
        self.ui.Ignoring_Logic_Table.showColumn(self.logic_tbl_model.miind)

        # The Right table of Ignored Macros
        self.ignored_model = MPSSortFilterModel(self)
        self.ignored_model.setSourceModel(self.logic_tbl_model)
        self.ui.Ignored_Logic_Table.setModel(self.ignored_model)

        self.ignored_model.setFilterByColumn(self.logic_tbl_model.numind, 'filter out everything')

        for i in range(3, self.logic_tbl_model.conind[-1] + 1):
            self.ui.Ignored_Logic_Table.hideColumn(i)

        self.ui.Ignored_Logic_Table.sortByColumn(0, Qt.AscendingOrder)

        # Sets up the selection details of a macro
        self.ignore_splitter_state = [1, 300]

        s = SelectionDetailsHelper(mpslogicmodel=self.model,
                                   rates_list=rates_list,
                                   tab_splitter=self.ui.Ignore_Vertical_Splitter,
                                   table_view=self.Ignored_Logic_Table,
                                   close_button=self.ui.Ignore_Selection_Close_Button,
                                   name_label=self.ui.Ignore_Name_Field,
                                   ignore_label=self.ui.Ignore_Ignored_When_Field,
                                   current_state_label=self.ui.Ignore_Current_State_Field,
                                   code_label=self.ui.Ignore_Code_Field,
                                   code_section_label=self.ui.Ignore_Code_Label,
                                   bypass_button=self.ui.Ignore_Bypass_Button,
                                   truth_table=self.ui.Ignore_Logic_Details_Truth_Table,
                                   pvs_table=self.ui.Ignore_Logic_Details_PVs_Table,
                                   logic_model=self.ignored_model, logic_tbl_model=self.logic_tbl_model,
                                   IOC_PREFIX=IOC_PREFIX)

        self.ignoreSelection = s

        hdr = self.ui.Ignoring_Logic_Table.horizontalHeader()
        hdr2 = self.ui.Ignored_Logic_Table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.resizeSection(self.logic_tbl_model.mmrind, 220)

        hdr2.setSectionResizeMode(QHeaderView.Interactive)
        hdr2.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr2.resizeSection(1, 200)

    def ignore_connections(self):
        """Set up slot connections for the Selection Details widget."""
        self.ui.Ignoring_Logic_Table.sortByColumn(self.logic_tbl_model.mmrind, Qt.AscendingOrder)
        self.ui.Ignoring_Logic_Table.sortByColumn(self.logic_tbl_model.miind, Qt.DescendingOrder)

        self.ui.Ignoring_Logic_Table.selectionModel().selectionChanged.connect(self.ignoring_selected)

        self.ignoreSelection.selection_connections()

    @Slot(QItemSelection, QItemSelection)
    def ignoring_selected(self, selected, deselected):
        """Slot called when a row is selected. This will change the
        Ignored Macros table and filter its content to the selected item."""
        indexes = selected.indexes()
        if not indexes:
            indexes = deselected.indexes()
        row_ind = self.ignoring_model.mapToSource(indexes[0])

        filter_text = str(self.logic_tbl_model._data[row_ind.row()][self.logic_tbl_model.numind])
        self.ignored_model.setFilterByColumn(self.logic_tbl_model.numind, filter_text)
