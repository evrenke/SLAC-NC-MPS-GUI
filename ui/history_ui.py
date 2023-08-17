from qtpy.QtCore import Qt, Slot
from qtpy.QtWidgets import QHeaderView, QApplication
from models.message_table_model import MessageTableModel, MPSSortFilterModel
from PyQt5.QtCore import QTimer, QDateTime
from functools import partial
from mps_constants import FROM_1970_TO_1990_IN_SECONDS


class HistoryUI():
    """
    author: Evren Keskin
    ===================================================================
    HistoryUI is the class that connects the message table model that
    turns the history of messages info to a table into the UI.
    It shows a select range of messages's with their times, and
    allows for UI updates based on range changes, text searches
    and a display for the row count of what is currently shown.
    ===================================================================
    """
    def history_init(self):
        """
        Initializer for everything in Logic tab: Message Table Model,
        Message Item Delegate, and the header.
        """
        self.live_message_tbl_model = MessageTableModel(self, self.messageModel)

        self.live_message_tbl_model.initialize_live()

        self.history_live_model = MPSSortFilterModel(self)
        self.history_live_model.setSourceModel(self.live_message_tbl_model)

        liveTable = self.ui.History_Table_View
        liveTable.setModel(self.history_live_model)

        hdr = liveTable.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)

        self.interactive_message_tbl_model = MessageTableModel(self, self.messageModel)

        self.history_interactive_model = MPSSortFilterModel(self)
        self.history_interactive_model.setSourceModel(self.interactive_message_tbl_model)

        interactiveTable = self.ui.History_Interactive_Table_View
        interactiveTable.setModel(self.history_interactive_model)

        hdr2 = interactiveTable.horizontalHeader()
        hdr2.setSectionResizeMode(QHeaderView.Stretch)

        self.show_history_live_row_count()
        self.show_history_interactive_row_count()

    def history_connections(self):
        """
        Establish PV and slot connections for the message model and
        live and interactive tabs.
        History connections allows for the table to update with a set timer
        It sets a callback for new messages, and allows for the table to update with a set range
        """
        # Live Tab Setup:
        # Establish connections for showing the row count
        self.history_live_model.rowsRemoved.connect(self.show_history_live_row_count)
        self.history_live_model.rowsInserted.connect(self.show_history_live_row_count)
        self.history_live_model.layoutChanged.connect(self.show_history_live_row_count)

        # Start a timer for live sql query updates here
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_live_table)
        self.flip_freeze()

        # Connect the freezing button to the list freezing function
        self.ui.Pause_Button.clicked.connect(self.flip_freeze)

        # Establish connections for showing the row count
        self.history_interactive_model.rowsRemoved.connect(self.show_history_interactive_row_count)
        self.history_interactive_model.rowsInserted.connect(self.show_history_interactive_row_count)
        self.history_interactive_model.layoutChanged.connect(self.show_history_interactive_row_count)

        # Interactive Tab Setup:
        # Establish connection for the name text search filtering
        self.ui.Interactive_Search_Line_Edit.textChanged.connect(
            partial(self.history_interactive_model.setFilterByColumn, 1))

        # Establish connection to search by time interval from calendars
        self.ui.History_Search_Button.clicked.connect(self.update_interval_table)

    @Slot()
    def flip_freeze(self):
        if self.timer.isActive():
            self.timer.stop()
            self.ui.Pause_Button.setText('Paused - Click To Continue Timer')
        else:
            self.update_live_table()
            self.timer.start(10000)  # 10 second timer, might change later if its too infrequent
            self.ui.Pause_Button.setText('Running - Click To Pause Timer')

    @Slot()
    def update_live_table(self):
        self.live_message_tbl_model.update_live()
        self.show_history_live_row_count()

    @Slot()
    def update_interval_table(self):

        # Change the cursor to a waiting icon, depending on SQL query period the wait can take a lot of time
        QApplication.setOverrideCursor(Qt.WaitCursor)

        startValue = QDateTime.toSecsSinceEpoch(self.ui.History_Start_Date_Time_Edit.dateTime())
        endValue = QDateTime.toSecsSinceEpoch(self.ui.History_End_Date_Time_Edit.dateTime())

        # Adjust for 1990
        startValue -= FROM_1970_TO_1990_IN_SECONDS
        endValue -= FROM_1970_TO_1990_IN_SECONDS

        # A valid search has some rules to for the times
        # Start time has to be less than the end time
        # End time has to be at most the current time, THE JAVA CODE PREVENTS TIME TRAVEL FOR SOME REASON
        # NO MESSAGES FROM THE FUTURE, SEND THOSE BACK TO THE FUTURE

        if startValue <= endValue:  # startValue is valid somehow and endValue is valid somehow
            self.interactive_message_tbl_model.update_interactive(startValue, endValue)
            self.show_history_interactive_row_count()

        QApplication.restoreOverrideCursor()

    @Slot()
    def show_history_live_row_count(self):
        """
        When the number of displayed rows changes, update the row
        count at the bottom of the tab.
        """
        rows = self.history_live_model.rowCount()
        self.ui.Live_Number_Filters_Label.setText(f"Displaying {rows} / {len(self.messageModel.liveMessages)} Messages")

    @Slot()
    def show_history_interactive_row_count(self):
        """
        When the number of displayed rows changes, update the row
        count at the bottom of the tab.
        """
        rows = self.history_interactive_model.rowCount()
        total = len(self.messageModel.interactiveMessages)
        self.ui.Interactive_Number_Filters_Label.setText(f"Displaying {rows} / {total} Messages")
