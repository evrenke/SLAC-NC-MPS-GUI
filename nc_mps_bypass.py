from pydm import Display
from functools import partial
from qtpy.QtCore import (QDateTime, Qt)
from qtpy.QtGui import QIntValidator
from qtpy.QtWidgets import (QWidget, QHBoxLayout, QCheckBox, QComboBox, QHeaderView, QTableWidgetItem, QMessageBox)
from epics import PV
import numpy
from datetime import datetime
from mps_constants import (BYPASS_VALUE_POSTFIX, STATE_IS_OK_POSTFIX,
                           BYPASS_DURATION_POSTFIX, BYPASS_FAULT_NUMBERS_POSTFIX,
                           BYPASS_SECONDS_POSTFIX, FROM_1970_TO_1990_IN_SECONDS)


class NC_MPS_Bypass(Display):
    """
    author: Evren Keskin
    ====================================================================================
    NC_MPS_Bypass is a class that creates a separate window for bypassing macros.

    Bypassing is the process of overriding the value of a current state of a fault
    with a passed value, for a passed duration of seconds.

    There are two varieties of the bypass window:
    1) For a non-code macro, which will bypass all faults of the macro
    for a given duration to a combobox chosen state.
    2) For a code macro, which will bypass chosen faults of a macro,
    each for their own new selected value, for a given duration.

    This class will adjust the UI based on either type of macro

    EDIT BEFORE FINISHING NC MPS GUI:
    ====================================================================================
    This is so far the only place where NC_MPS_GUI ever writes into a PV rather than just read.
    It has been adjusted to not make that writing for now.
    """
    def __init__(self, parent=None, args=[], macros=None, ui_filename=None):
        super(NC_MPS_Bypass, self).__init__(parent=None, args=None,
                                            macros=None, ui_filename='ui/nc_mps_bypass.ui')

        # Change the window elements for a code macro, so the only table is the fault specific bypasser
        if macros['DEVICE_IS_CODE'] == 1:
            self.device_hdr = ["Bit", "Current Value", "Is Bypassed", "Expiration Date", "Bypass", "New Value"]
            self.ui.bypass_code_values_table.setColumnCount(len(self.device_hdr))
            self.ui.bypass_code_values_table.setHorizontalHeaderLabels(self.device_hdr)

            hdr = self.ui.bypass_code_values_table.horizontalHeader()
            hdr.setSectionResizeMode(QHeaderView.Interactive)
            hdr.setSectionResizeMode(0, QHeaderView.Stretch)
            hdr.setSectionResizeMode(2, QHeaderView.Fixed)

            self.pop_code_values_table(macros['DEVICE_OK_STATES'],
                                       macros['DEVICE_FAULTED_STATES'],
                                       macros['DEVICE_FAULT_PVS'],
                                       macros['DEVICE_FAULT_NUMBERS'],
                                       macros['IOC_PREFIX'])
            self.ui.bypass_values_table.hide()
            self.ui.bypass_states_label.hide()
            self.ui.bypass_states_combobox.hide()
            self.ui.min_rate_limit_label.hide()
            self.resize(800, self.size().height())
        # Change the window elements for a non-code macro, so the only table is the pv and value table
        else:
            self.device_hdr = ["Device", "Value"]
            self.ui.bypass_values_table.setColumnCount(len(self.device_hdr))
            self.ui.bypass_values_table.setHorizontalHeaderLabels(self.device_hdr)

            hdr = self.ui.bypass_values_table.horizontalHeader()
            hdr.setSectionResizeMode(QHeaderView.Interactive)
            hdr.setSectionResizeMode(0, QHeaderView.Stretch)
            self.set_states_combo_box(macros['DEVICE_MACRO_STATES'], macros['DEVICE_MACRO_STATE_MINS'])
            self.pop_values_table(macros['DEVICE_CURRENT_STATE_NUMBER'], macros['DEVICE_FAULT_PVS'])
            self.ui.bypass_code_values_table.hide()

        self.ui.bypassed_device_name.setText(macros['DEVICE_NAME'])

        # Set up limits for duration setting: calendar has to be past current time
        # Duration has to be above 0
        self.ui.bypass_expiration_calendar.setMinimumDateTime(QDateTime.currentDateTime())
        self.bypass_duration_value.setValidator(QIntValidator(bottom=0))

        self.check_code_macro_info(macros['DEVICE_IS_CODE'])

        self.check_cancel_bypass_options(macros['DEVICE_FAULT_PVS'],
                                         macros['DEVICE_IS_CODE'],
                                         macros['DEVICE_FAULT_NUMBERS'],
                                         macros['IOC_PREFIX'])

        # Connect the calendar to modify the duration number display
        # And connect the duration number display to do a bypass on 'Enter' press
        self.ui.bypass_expiration_calendar.editingFinished.connect(partial(self.set_duration_from_calendar))

        self.ui.bypass_duration_value.returnPressed.connect(partial(self.attempt_bypass, macros['DEVICE_IS_CODE'],
                                                                    macros['DEVICE_FAULT_PVS'],
                                                                    macros['DEVICE_OK_STATES'],
                                                                    macros['DEVICE_FAULTED_STATES'],
                                                                    macros['DEVICE_FAULT_NUMBERS'],
                                                                    macros['IOC_PREFIX']))

    def check_code_macro_info(self, is_code):
        """
        Hides code instructions on non-code macros
        """
        if is_code != 1:
            self.ui.code_info_label.hide()
            self.ui.code_instructions_label.hide()

    def pop_values_table(self, current_state_number, fault_pvs):
        """Populate the values table. The values table holds a fault pv
        and its related bit value based on the current state of the macro"""
        self.ui.bypass_values_table.setRowCount(len(fault_pvs))
        for i, fault_pv in enumerate(fault_pvs):
            pv_item = CellItem(fault_pv)

            value_str = self.get_bit_at(current_state_number, i)
            bypassed_value_item = CellItem(str(value_str))

            self.ui.bypass_values_table.setItem(i, 0, pv_item)
            self.ui.bypass_values_table.setItem(i, 1, bypassed_value_item)

    def pop_code_values_table(self, ok_states, faulted_states, fault_pvs, fault_numbers, IOC_PREFIX):
        """Populate the code values table. The code values table
        allows users to set the bypassing by bit values, and gives additional buttons for this input
        Each row will show the actual fault pv, the current fault pv as the screen is opened,
        and a combo box for choosing a state to bypass to"""

        self.checkBoxes = []
        self.comboBoxes = []

        self.ui.bypass_code_values_table.setRowCount(len(fault_pvs))
        for i, fault_pv in enumerate(fault_pvs):
            pv_item = CellItem(fault_pv)

            faultvalue = PV(fault_pv + STATE_IS_OK_POSTFIX).get()

            state_combobox_widget = QComboBox()
            state_combobox_widget.addItem(ok_states[i])
            state_combobox_widget.addItem(faulted_states[i])

            self.comboBoxes.append(state_combobox_widget)

            current_state_item = CellItem(state_combobox_widget.itemText(int(faultvalue)))

            will_bypass_item = QCheckBox()
            will_bypass_item.setChecked(True)

            is_bypassed = PV(fault_pv + BYPASS_VALUE_POSTFIX).get()
            is_bypassed_text = 'YES'
            if is_bypassed == 0:
                will_bypass_item.setChecked(False)
                is_bypassed_text = 'NO'
            is_bypassed_item = CellItem(is_bypassed_text)

            bypassed_faults = PV(IOC_PREFIX + BYPASS_FAULT_NUMBERS_POSTFIX).value
            seconds = PV(IOC_PREFIX + BYPASS_SECONDS_POSTFIX).value

            if fault_numbers[i] in bypassed_faults:
                second_index = numpy.where(bypassed_faults == fault_numbers[i])[0]
                duration = seconds[second_index][0] + FROM_1970_TO_1990_IN_SECONDS
                exp_date = datetime.fromtimestamp(duration).strftime("%A, %B %d, %Y %I:%M:%S")
            else:
                exp_date = '-'

            expiration_date_item = CellItem(exp_date)

            bypass_checkox_widget = QWidget()
            layout = QHBoxLayout()
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(will_bypass_item)
            bypass_checkox_widget.setLayout(layout)
            self.checkBoxes.append(will_bypass_item)

            # Set the base value of the buttons based on the given current state of the faults
            # Columns to set: ["Bit", "Current Value", "Is Bypassed", "New Value", "Bypass Duration Left", "Bypass"]
            self.ui.bypass_code_values_table.setItem(i, 0, pv_item)
            self.ui.bypass_code_values_table.setItem(i, 1, current_state_item)
            self.ui.bypass_code_values_table.setItem(i, 2, is_bypassed_item)
            self.ui.bypass_code_values_table.setItem(i, 3, expiration_date_item)
            self.ui.bypass_code_values_table.setCellWidget(i, 4, bypass_checkox_widget)
            self.ui.bypass_code_values_table.setCellWidget(i, 5, state_combobox_widget)

    def get_bit_at(self, number: int, index: int):
        """
        Gets a bitwise value for a pv using a given state number
        """
        while (index > 0):
            number = number >> 1
            index -= 1
        return number % 2

    def set_states_combo_box(self, state_names, state_mins):
        """
        For non-code macro, sets the combo box to have a list of the possible states of the macro
        """
        self.ui.bypass_states_combobox.addItems(state_names)
        self.update_min_rate_label(state_mins)
        self.ui.bypass_states_combobox.currentIndexChanged.connect(partial(self.update_min_rate_label, state_mins))

    def update_min_rate_label(self, state_mins):
        """
        A small label for the min rate of the selected combo box state
        """
        self.ui.min_rate_limit_label.setText('will rate limit to ' +
                                             state_mins[self.ui.bypass_states_combobox.currentIndex()])

    def check_cancel_bypass_options(self, pvs, is_code, fault_numbers, IOC_PREFIX):
        """
        Either hides the cancel bypass options, or shows them with a given PV
        This logic only really works for a non-code macro to bypass
        """
        if is_code != 1:  # non-code macro
            # we can always check the first one, and assume that all faults are passed
            # firstFaultBypassed = PV(pvs[0] + BYPASS_VALUE_POSTFIX).get()
            first_fault_num = fault_numbers[0]
            bypassed_faults = PV(IOC_PREFIX + BYPASS_FAULT_NUMBERS_POSTFIX).value
            seconds = PV(IOC_PREFIX + BYPASS_SECONDS_POSTFIX).value
            if first_fault_num not in bypassed_faults:  # not bypassed
                self.ui.cancel_bypass_button.hide()
                self.ui.bypass_exp_time_label.hide()
                self.ui.bypass_exp_date_time.hide()
            else:  # attach info about an existing bypass duration
                # For checking bypassing, we need to check the fault id in the bypassed list
                index_of_a_second = numpy.where(bypassed_faults == first_fault_num)[0]
                firstDuration = seconds[index_of_a_second][0] + FROM_1970_TO_1990_IN_SECONDS

                exp_date = datetime.fromtimestamp(firstDuration)
                self.ui.bypass_exp_date_time.setText(str(exp_date))
                self.ui.cancel_bypass_button.clicked.connect(partial(self.cancelAllBypasses,
                                                                     pvs,
                                                                     is_code,
                                                                     fault_numbers,
                                                                     IOC_PREFIX))
        else:  # code macro
            # Check if ANY fault is bypassed
            lowestDuration = None

            # To set the duration, we find the lowest bypass duration of any of the faults
            # So, if a code macro were to have many various durations, the lowest is shown
            # 'lowestDuration' is the second count from the Epoch (Jan 1st 1970)
            bypassed_faults = PV(IOC_PREFIX + BYPASS_FAULT_NUMBERS_POSTFIX).value
            seconds = PV(IOC_PREFIX + BYPASS_SECONDS_POSTFIX).value
            for fault_num in fault_numbers:
                if fault_num in bypassed_faults:
                    index_of_a_second = numpy.where(bypassed_faults == fault_num)[0]
                    if lowestDuration is None or lowestDuration > seconds[index_of_a_second][0]:
                        lowestDuration = seconds[index_of_a_second][0] + FROM_1970_TO_1990_IN_SECONDS

            if lowestDuration is None:
                self.ui.bypass_exp_time_label.hide()
                self.ui.bypass_exp_date_time.hide()
                self.ui.cancel_bypass_button.hide()
            else:
                exp_date = datetime.fromtimestamp(lowestDuration)
                self.ui.bypass_exp_date_time.setText(exp_date)
                self.ui.cancel_bypass_button.clicked.connect(partial(self.cancelAllBypasses,
                                                                     pvs,
                                                                     is_code,
                                                                     fault_numbers,
                                                                     IOC_PREFIX))

    def set_duration_from_calendar(self):
        """
        Changes the duration value based on a calendar edit,
        with the current time of launching this window taken as "the origin"
        """
        duration = QDateTime.currentDateTime().secsTo(self.ui.bypass_expiration_calendar.dateTime())
        if duration >= 0:
            durationStr = str(duration)
            self.ui.bypass_duration_value.setText(durationStr)

    def attempt_bypass(self, is_code, pvs, ok_states, fault_states, fault_numbers, IOC_PREFIX):
        """
        Uses values passed to this class about the macro device
        And the selections of time, and value from the user
        To do a bypass on both non-code or macros
        Bypass to selected state for non-code, and selected bit values for code
        """
        failed_bypass = False
        messagesLogged = []
        popupMessage = ''

        for i, pv in enumerate(pvs):
            # Either bypass all faults of a non-code, or only the checked of a code macro
            # Ensure that there is a number to look at as duration
            if self.ui.bypass_duration_value.text().isdigit() and (is_code != 1 or self.checkBoxes[i].isChecked()):
                duration = int(self.ui.bypass_duration_value.text())
                date = QDateTime.currentDateTime().addSecs(int(self.ui.bypass_duration_value.text()))

                value = ''
                state = ''
                if is_code != 1:
                    bypass_state_number = self.ui.bypass_states_combobox.currentIndex()
                    state = self.ui.bypass_states_combobox.currentText()
                    value = self.get_bit_at(bypass_state_number, i)
                else:
                    value = self.comboBoxes[i].currentIndex()
                    if value == 0:
                        state = ok_states[i]
                    else:
                        state = fault_states[i]

                duration = int(self.ui.bypass_duration_value.text())
                if duration != 0:
                    writingDurationPV = PV(pv + BYPASS_DURATION_POSTFIX)

                    popupMessage += f'{pv} bypassed to {state} ({value}) until {date.toString()} ({duration})\n'
                    messagesLogged.append(f'{pv} bypassed to {state} ({value}) until {date.toString()} ({duration})')
                    if writingDurationPV.write_access:
                        writingDurationPV.put(duration)

                        writingValuePV = PV(pv + BYPASS_VALUE_POSTFIX)
                        writingValuePV.put(value)
                    else:

                        failed_bypass = True

        if failed_bypass:
            errorMessageBox = QMessageBox()
            errorMessageBox.setText('CANNOT BYPASS, NO WRITE ACCESS')
            errorMessageBox.setWindowTitle('BYPASS ERROR')
            errorMessageBox.setStandardButtons(QMessageBox.Ok)
            errorMessageBox.setDetailedText('what would have been logged:\n' + popupMessage)
            errorMessageBox.exec()
        else:
            successMessageBox = QMessageBox()
            successMessageBox.setWindowTitle('Successful Bypass')
            successMessageBox.setText('BYPASS SUCCESSFUL')
            successMessageBox.setDetailedText('what would have been logged:\n' + popupMessage)
            successMessageBox.exec()
            # TEMPORARY TEMPORARY TEMPORARY TEMPORARY TEMPORARY
            # messagesLogged needs to be logged here, like the java MessageLogAPI does!!!!!!!!!!

        if is_code == 1:
            self.pop_code_values_table(ok_states, fault_states, pvs, fault_numbers, IOC_PREFIX)
        else:
            self.pop_values_table(bypass_state_number, pvs)
        self.check_cancel_bypass_options(pvs, is_code, fault_numbers, IOC_PREFIX)

    def cancelAllBypasses(self, fault_pvs, is_code, fault_numbers, IOC_PREFIX):
        """
        Sets all of the fault pvs of value and duration to 0.
        This removes the bypass by ending it
        """
        failed_cancel = False
        messagesLogged = []
        popupMessage = ''
        for fault_pv in fault_pvs:
            writingDurationPV = PV(fault_pv + BYPASS_DURATION_POSTFIX)
            messagesLogged.append(f'{fault_pv} bypassed cancelled to ({0}) with value ({0})')
            popupMessage += f'{fault_pv} bypassed cancelled to ({0}) with value ({0})\n'
            if writingDurationPV.write_access:
                writingDurationPV.put(0)
            else:
                failed_cancel = True

        if failed_cancel:
            errorMessageBox = QMessageBox()
            errorMessageBox.setText('CANNOT BYPASS, NO WRITE ACCESS')
            errorMessageBox.setWindowTitle('BYPASS CANCEL ERROR')
            errorMessageBox.setStandardButtons(QMessageBox.Ok)
            errorMessageBox.setDetailedText('what would have been logged:\n' + popupMessage)
            errorMessageBox.exec()
        else:
            successMessageBox = QMessageBox()
            successMessageBox.setWindowTitle('Successful Bypass Cancel')
            successMessageBox.setDetailedText('what would have been logged:\n' + popupMessage)
            successMessageBox.exec()

        self.check_cancel_bypass_options(fault_pvs, is_code, fault_numbers, IOC_PREFIX)


class CellItem(QTableWidgetItem):
    """Personalized QTableWidgetItem that sets preferred settings."""
    def __init__(self, text: str, *args, **kwargs):
        super(CellItem, self).__init__(text, *args, **kwargs)
        self.setTextAlignment(Qt.AlignCenter)
        self.setBackground(Qt.white)
