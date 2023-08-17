from qtpy.QtCore import (Qt, Slot, QPoint)
from qtpy.QtWidgets import (QHeaderView, QAction, QMenu, QTableView)
from models.logic_table_model import MPSSortFilterModel


class SummaryUI:
    """
    author: Evren Keskin
    ===================================================================
    SummaryUI is the class that uses logic table model
    to make 2 tables for summary of relevant macro information.
    The first table is Logic Summary, that shows only items with issues.
    The second table is Bypassed Faults, that shows macros with bypassed faults
    and their expiration dates.
    ===================================================================
    """
    def summary_init(self, is_cud=False):
        """Initializer for everything in the Summary tab: Summary table,
        Bypass table, and Custom Context menus."""
        # Initialize the Summary Logic Table and Headers
        self.summ_model = MPSSortFilterModel(self)
        self.summ_model.setSourceModel(self.logic_tbl_model)
        self.summ_model.setFilterByColumn(2, "This text is just a confirmation of filtering by min rate status,\
                                           I could put the bee movie script here if I wanted")
        self.summ_model.setFilterByColumn(self.logic_tbl_model.iind, "N")
        self.summ_model.setFilterByColumn(self.logic_tbl_model.aeind, 'N')
        self.ui.Logic_Summary_Table.setModel(self.summ_model)
        for i in range(self.logic_tbl_model.conind[0], self.logic_tbl_model.conind[-1] + 1):
            self.ui.Logic_Summary_Table.hideColumn(i)
        self.ui.Logic_Summary_Table.sortByColumn(0, Qt.AscendingOrder)
        self.ui.Logic_Summary_Table.setItemDelegate(self.delegate)

        hdr = self.ui.Logic_Summary_Table.horizontalHeader()
        if not is_cud:
            hdr.setSectionResizeMode(QHeaderView.Interactive)
            hdr.setSectionResizeMode(0, QHeaderView.Stretch)
            hdr.resizeSection(1, 200)
        else:
            font = hdr.font()
            font.setPointSize(16)
            hdr.setFont(font)
            hdr.setFixedHeight(40)
            hdr.resizeSection(0, 550)
            hdr.resizeSection(1, 300)
            hdr.setSectionResizeMode(8, QHeaderView.Stretch)

        # Initialize the Bypass Table and Headers
        self.byp_model = MPSSortFilterModel(self)
        self.byp_model.setSourceModel(self.logic_tbl_model)
        self.byp_model.setFilterByColumn(self.logic_tbl_model.bind, "Y")
        self.ui.Bypassed_Summary_Table.setModel(self.byp_model)
        for i in range(2, self.logic_tbl_model.conind[-1] + 1):
            self.ui.Bypassed_Summary_Table.hideColumn(i)
        self.ui.Bypassed_Summary_Table.showColumn(self.logic_tbl_model.beind)
        self.ui.Bypassed_Summary_Table.sortByColumn(self.logic_tbl_model.beind, Qt.AscendingOrder)
        self.ui.Bypassed_Summary_Table.setItemDelegate(self.delegate)

        hdr = self.ui.Bypassed_Summary_Table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)

        if is_cud:
            print('make some enlargement here?')
            # font = hdr.font()
            # font.setPointSize(14)
            # hdr.setFont(font)
            # hdr.setFixedHeight(40)

        # Initialize the QAction used by the context menus
        if not is_cud:
            self.selected_macro = None
            self.action = QAction("Open fault in Logic tab", self)
            self.menu = QMenu(self)
            self.menu.addAction(self.action)

    def summ_connections(self):
        """
        Establish connections for the context menus and their action.
        """
        self.ui.Logic_Summary_Table.customContextMenuRequested.connect(
            self.custom_context_menu)
        self.ui.Bypassed_Summary_Table.customContextMenuRequested.connect(
            self.custom_context_menu)
        self.action.triggered.connect(self.logic_select)

    def logic_select(self):
        """
        Set the selected fault in the Logic Tab to open the
        SelectionDetails widget. Then change tabs to the Logic Tab.
        """
        self.ui.Logic_Search_Line_Edit.setText("")
        index = self.logic_model.mapFromSource(self.selected_macro)
        self.ui.Logic_Table_View.setCurrentIndex(index)
        self.ui.Logic_Table_View.scrollTo(index)
        self.ui.Main_Tab_Widget.setCurrentIndex(2)

    @Slot(QPoint)
    def custom_context_menu(self, pos: QPoint):
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
            source_index = table.model().mapToSource(index)
            self.selected_macro = (self.logic_model.sourceModel()
                                   .index(source_index.row(), 0))
            self.menu.popup(table.viewport().mapToGlobal(pos))
