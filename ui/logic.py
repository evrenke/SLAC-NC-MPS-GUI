from functools import partial
from qtpy.QtCore import (Qt, Slot)
from qtpy.QtWidgets import QHeaderView

from models.logic_table_model import MPSSortFilterModel
from ui.selection_detail import SelectionDetailsHelper


class LogicUI():
    """
    author: Evren Keskin
    ===================================================================
    LogicUI is the class that connects the logic table model that
    turns the model of macro info to a table into the UI.
    It shows the full list of macro's with their current states, and
    allows for UI updates based on current state changes, text searches
    and a display for the row count of what is currently shown.
    ===================================================================
    """
    def logic_init(self, rates_list, IOC_PREFIX):
        """
        Initializer for everything in Logic tab: Logic Table Model,
        Logic Item Delegate, and the headers.
        """
        # self.logic_tbl_model = LogicTableModel(self, self.model, IOC_PREFIX=IOC_PREFIX)

        self.logic_model = MPSSortFilterModel(self)
        self.logic_model.setSourceModel(self.logic_tbl_model)
        self.logic_model.setFilterByColumn(self.logic_tbl_model.aeind, 'N')

        self.pvs = []

        logicUITableView = self.ui.Logic_Table_View
        logicUITableView.setModel(self.logic_model)
        logicUITableView.setItemDelegate(self.delegate)
        for i in range(self.logic_tbl_model.conind[1], self.logic_tbl_model.conind[-1] + 1):
            logicUITableView.hideColumn(i)

        s = SelectionDetailsHelper(mpslogicmodel=self.model, rates_list=rates_list,
                                   tab_splitter=self.ui.Logic_Tab_Splitter,
                                   table_view=logicUITableView, close_button=self.ui.Logic_Selection_Close_Button,
                                   name_label=self.ui.Logic_Name_Field,
                                   ignore_label=self.ui.Logic_Ignored_When_Field,
                                   current_state_label=self.ui.Logic_Current_State_Field,
                                   code_label=self.ui.Logic_Code_Field,
                                   code_section_label=self.ui.Logic_Code_Label,
                                   bypass_button=self.ui.Logic_Bypass_Button,
                                   truth_table=self.ui.Logic_Details_Truth_Table,
                                   pvs_table=self.ui.Logic_Details_PVs_Table,
                                   logic_model=self.logic_model, logic_tbl_model=self.logic_tbl_model,
                                   IOC_PREFIX=IOC_PREFIX)

        self.logicSelectionDetailHelper = s

        self.ui.Cyan_Button.hide()
        self.ui.Snake_Button.hide()
        self.isCyan = False

        self.logic_model.setFilterByColumn(0, "")
        logicUITableView.sortByColumn(0, Qt.AscendingOrder)

        hdr = logicUITableView.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.resizeSection(2, 100)

        self.show_row_count()

    def logic_connections(self, IOC_PREFIX=None):
        """
        Establish PV and slot connections for the logic model and
        logic tab.
        Logic connections allows for the table to update to the current states of each device
        It sets a partial callback for changes, and allows for the table to update as it needs to
        """

        self.logicSelectionDetailHelper.selection_connections()

        # Establish connections for showing the row count
        self.logic_model.rowsRemoved.connect(self.show_row_count)
        self.logic_model.rowsInserted.connect(self.show_row_count)
        self.logic_model.layoutChanged.connect(self.show_row_count)

        # Establish connection for the name text search filtering
        self.ui.Logic_Search_Line_Edit.textChanged.connect(partial(self.logicTextSearch))

        # Establish the cyan modulation connection:
        self.ui.Cyan_Button.clicked.connect(self.modulateCyan)

    @Slot()
    def show_row_count(self):
        """
        When the number of displayed rows changes, update the row
        count at the bottom of the tab.
        """
        rows = self.logic_model.rowCount()
        self.ui.Logic_Number_Filters_Label.setText(f'Displaying {rows} / {len(self.model.numbersToPreppedDevices)} Macros')

    @Slot()
    def logicTextSearch(self, text):
        self.logic_model.setFilterByColumn(0, text)
        if text.lower() == 'cyan modulator':
            print('this is where the fun begins')
            self.ui.Cyan_Button.show()
            self.ui.Snake_Button.hide()
        elif text.lower() == 'snake':
            self.ui.Cyan_Button.hide()
            self.ui.Snake_Button.show()
        else:
            self.ui.Cyan_Button.hide()
            self.ui.Snake_Button.hide()

    @Slot()
    def modulateCyan(self):
        if not self.isCyan:
            print('Did you ever hear the tragedy of Darth Plagueis The Cyan?')
            print('I thought not. It`s not a story the AD EED would tell you.')
            print('It`s a Sith legend. Darth Plagueis was a Cyan Lord of the Sith')
            print('so powerful and so wise he could use the Cyan to influence the midichlorians to create life...')
            print('He had such a knowledge of the cyan side that he could even keep the ones he cared about from dying')
            self.ui.setStyleSheet('font-weight: bold;background-color: cyan; alternate-background-color: gray')
            self.ui.Cyan_Button.setText('Deactivate Cyan Modulator')
            self.isCyan = True
        else:
            print('The dark side of the Cyan is a pathway to many abilities some consider to be unnatural.')
            print('He became so powerful... the only thing he was afraid of was losing his cyan,')
            print('which eventually, of course, he did. Unfortunately, he taught his apprentice everything he knew,')
            print('then his apprentice killed him in his sleep.')
            print('Ironic. He could save others from Cyan, but not himself')
            self.ui.setStyleSheet('font-weight: bold')
            self.ui.Cyan_Button.setText('Activate Cyan Modulator')
            self.isCyan = False
