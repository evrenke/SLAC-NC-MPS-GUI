import numpy as np
from datetime import datetime
from functools import partial
from qtpy.QtGui import QIntValidator
from qtpy.QtCore import (QDateTime, Qt, Slot)
from qtpy.QtWidgets import (QWidget, QHBoxLayout, QCheckBox, QComboBox, QHeaderView, QTableWidgetItem, QMessageBox)
from epics import PV
from pydm import Display
import mps_constants as const


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
        super(NC_MPS_Bypass, self).__init__(parent=parent, args=args,
                                            macros=macros, ui_filename='ui/nc_mps_bypass.ui')

        self.init_macros(macros)
        self.init_ui()
        self.populate_values_table()
        self.init_slots()

    def init_macros(self, macros):
        self.ioc_prefix = macros['IOC_PREFIX']
        self.byp_ids = PV(self.ioc_prefix + const.BYPASS_FAULT_NUMBERS_POSTFIX)
        self.byp_durations = PV(self.ioc_prefix + const.BYPASS_SECONDS_POSTFIX)

        self.is_code = macros['DEVICE_IS_CODE'] == 1
        self.device_name = macros['DEVICE_NAME']
        self.current_state = macros['DEVICE_CURRENT_STATE_NUMBER']

        self.macro_states = []
        for i in range(len(macros['DEVICE_MACRO_STATES'])):
            macro_dict = {}
            macro_dict['state'] = macros['DEVICE_MACRO_STATES'][i]
            macro_dict['min_rate'] = macros['DEVICE_MACRO_STATE_MINS'][i]
            self.macro_states.append(macro_dict)

        self.fault_states = []
        for i in range(len(macros['DEVICE_FAULT_PVS'])):
            fault_dict = {}
            fault_dict['pvname'] = macros['DEVICE_FAULT_PVS'][i]
            fault_dict['id'] = macros['DEVICE_FAULT_NUMBERS'][i]
            fault_dict['ok_state'] = macros['DEVICE_OK_STATES'][i]
            fault_dict['fault_state'] = macros['DEVICE_FAULTED_STATES'][i]
            fault_dict['fault_pv'] = PV(fault_dict['pvname'] + const.STATE_IS_OK_POSTFIX)
            fault_dict['byp_pv'] = PV(fault_dict['pvname'] + const.BYPASS_VALUE_POSTFIX)
            fault_dict['byp_dur_pv'] = PV(fault_dict['pvname'] + const.BYPASS_DURATION_POSTFIX)
            self.fault_states.append(fault_dict)

    def init_ui(self):
        self.ui.byp_dev_lbl.setText(self.device_name)

        if not self.is_code:
            device_hdr = ["Device", "Current Value", " New Value"]
            self.ui.code_logic_frame.hide()
        else:
            device_hdr = ["Bit", "Current Value", "Is Bypassed", "Expiration", "Bypass", "New Value"]
            self.ui.byp_states_lbl.hide()
            self.ui.byp_states_cmbx.hide()
            self.ui.min_rate_lbl.hide()
            self.resize(800, self.size().height())

        self.ui.byp_val_tbl.setColumnCount(len(device_hdr))
        self.ui.byp_val_tbl.setHorizontalHeaderLabels(device_hdr)

        hdr = self.ui.byp_val_tbl.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)

        states = [ms['state'] for ms in self.macro_states]
        self.ui.byp_states_cmbx.addItems(states)
        self.ui.byp_states_cmbx.setCurrentIndex(self.current_state)
        self.update_state(self.current_state)

        self.ui.byp_exp_cal.setMinimumDateTime(QDateTime.currentDateTime())
        self.ui.byp_duration_edt.setValidator(QIntValidator(bottom=0))

    def init_slots(self):
        self.ui.byp_states_cmbx.currentIndexChanged.connect(self.update_state)

        self.ui.byp_exp_cal.dateTimeChanged.connect(self.duration_matching)
        self.ui.byp_exp_cal.returnPressed.connect(self.bypass)
        self.ui.byp_duration_edt.editingFinished.connect(self.duration_matching)
        self.ui.byp_duration_edt.returnPressed.connect(self.bypass)

        self.ui.cancel_byp_btn.clicked.connect(partial(self.bypass, cancel=True))

        for i, fault in enumerate(self.fault_states):
            fault['fault_pv'].add_callback(partial(self.update_current_val, row=i), run_now=True)
            fault['byp_pv'].add_callback(self.populate_exp_frame, run_now=True)

            if self.is_code:
                fault['byp_pv'].add_callback(partial(self.update_is_byp, row=i, id=fault['id']), run_now=True)

    def populate_values_table(self):
        self.comboboxes = []
        self.checkboxes = []

        self.ui.byp_val_tbl.setRowCount(len(self.fault_states))

        for i, fault in enumerate(self.fault_states):
            pv_item = CellItem(fault['pvname'])
            self.ui.byp_val_tbl.setItem(i, 0, pv_item)

            if not self.is_code:
                byp_val = (self.current_state & (0b1 << i)) >> i
                byp_val_item = CellItem(str(byp_val))
                self.ui.byp_val_tbl.setItem(i, 2, byp_val_item)
                continue

            byp_checkbox = QCheckBox()
            byp_checkbox.setChecked(fault['id'] in self.byp_ids.value)
            self.checkboxes.append(byp_checkbox)

            byp_checkbox_wid = QWidget()
            layout = QHBoxLayout()
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(byp_checkbox)
            byp_checkbox_wid.setLayout(layout)

            state_combobox = QComboBox()
            state_combobox.addItems((fault['ok_state'], fault['fault_state']))
            state_combobox.setCurrentIndex(fault['byp_pv'].value)
            self.comboboxes.append(state_combobox)

            self.ui.byp_val_tbl.setCellWidget(i, 4, byp_checkbox_wid)
            self.ui.byp_val_tbl.setCellWidget(i, 5, state_combobox)

    def populate_exp_frame(self, **kw):
        fault_ids = [f['id'] for f in self.fault_states]
        byp_ind = np.where(np.isin(self.byp_ids.value, fault_ids))[0].tolist()

        if not byp_ind:
            self.ui.byp_exp_frame.hide()
            return

        min_duration = int(min([self.byp_durations.value[i] for i in byp_ind]))
        duration = min_duration + const.FROM_1970_TO_1990_IN_SECONDS
        exp_qdt = QDateTime.fromSecsSinceEpoch(duration)
        exp_date = datetime.fromtimestamp(duration)
        remaining = QDateTime.currentDateTime().secsTo(exp_qdt)

        self.ui.byp_exp_cal.setDateTime(exp_qdt)
        self.ui.byp_duration_edt.setText(str(remaining))
        self.ui.byp_exp_datetime.setText(str(exp_date))

    def bypass_message(self, main_text, details):
        msg_dialog = QMessageBox()
        msg_dialog.setWindowTitle(main_text)
        msg_dialog.setText(main_text)
        msg_dialog.setStandardButtons(QMessageBox.Ok)
        msg_dialog.setDetailedText('\n'.join(details))
        msg_dialog.exec()

    @Slot()
    def bypass(self, cancel=False):
        dialog_details = []

        if cancel:
            byp_duration = 0
        else:
            try:
                byp_duration = int(self.ui.byp_duration_edt.text())
                if byp_duration <= 0:
                    raise ValueError
            except ValueError:
                self.bypass_message("BYPASS FAILED", ["[FAILED] Invalid bypass duration"])
                return

        write_pvs = []
        for i, fault in enumerate(self.fault_states):
            if (self.is_code and not self.checkboxes[i].isChecked()):
                continue
            elif cancel:
                byp_val = 0
            elif self.is_code:
                byp_val = self.comboboxes[i].currentIndex()
            else:
                byp_state_ind = self.ui.byp_states_cmbx.currentIndex()
                byp_val = (byp_state_ind & (0b1 << i)) >> i

            write_pvs.append((fault, byp_val))

        for fault, _ in write_pvs:
            for k in ['byp_pv', 'byp_dur_pv']:
                if not fault[k].write_access:
                    dialog_details.append(f"[FAILED] Unable to write to {fault[k].pvname}")

        if dialog_details:
            main_text = "BYPASS FAILED" if not cancel else "BYPASS CANCEL FAILED"
            self.bypass_message(main_text, dialog_details)
            return

        for fault, byp_val in write_pvs:
            if not cancel:
                fault['byp_pv'].value = byp_val

            fault['byp_dur_pv'].value = byp_duration
            dialog_details.append("[SUCCESS] Successfully bypassed "
                                  + f"{fault['byp_pv'].pvname} for "
                                  + f"{byp_duration} seconds")

        main_text = "BYPASS SUCCEEDED" if not cancel else "BYPASS CANCEL SUCCEEDED"
        self.bypass_message(main_text, dialog_details)

    def update_current_val(self, value, row, **kw):
        if not self.is_code:
            item = CellItem(str(int(value)))
        else:
            print(row, value)
            state = self.comboboxes[row].itemText(value)
            item = CellItem(state)
        self.ui.byp_val_tbl.setItem(row, 1, item)

    def update_is_byp(self, value, row, id, **kw):
        item = CellItem("YES" if value else "NO")
        self.ui.byp_val_tbl.setItem(row, 2, item)

        if id not in self.byp_ids.value:
            exp = '-'
        else:
            second_index = np.where(self.byp_ids.value == id)[0]
            duration = self.byp_durations.value[second_index][0] + const.FROM_1970_TO_1990_IN_SECONDS
            exp = datetime.fromtimestamp(duration).strftime("%A, %B %d, %Y %I:%M:%S")
        item = CellItem(exp)
        self.ui.byp_val_tbl.setItem(row, 3, item)

    @Slot(int)
    def update_state(self, index):
        for i in range(self.byp_val_tbl.rowCount()):
            item = CellItem(str((index & (0b1 << i)) >> i))
            self.ui.byp_val_tbl.setItem(i, 2, item)

        rate = self.macro_states[index]['min_rate']
        self.ui.min_rate_lbl.setText(f"Will limit rate to {rate}")

    @Slot()
    @Slot(QDateTime)
    def duration_matching(self, new_duration=None):
        curr = QDateTime.currentDateTime()
        if not new_duration:
            new_duration = self.ui.byp_duration_edt.text()
            new_duration = int(new_duration) if new_duration else 0
            new_dt = curr.addSecs(new_duration)

            self.ui.byp_exp_cal.blockSignals(True)
            self.ui.byp_exp_cal.setDateTime(new_dt)
            self.ui.byp_exp_cal.blockSignals(False)
        elif isinstance(new_duration, QDateTime):
            new_duration = curr.secsTo(new_duration)
            if new_duration < 0:
                self.ui.byp_exp_cal.blockSignals(True)
                self.ui.byp_exp_cal.setDateTime(curr)
                self.ui.byp_exp_cal.blockSignals(False)
                return

            self.ui.byp_duration_edt.blockSignals(True)
            self.ui.byp_duration_edt.setText(str(new_duration))
            self.ui.byp_duration_edt.blockSignals(False)


class CellItem(QTableWidgetItem):
    """Personalized QTableWidgetItem that sets preferred settings."""
    def __init__(self, text: str, *args, **kwargs):
        super(CellItem, self).__init__(text, *args, **kwargs)
        self.setTextAlignment(Qt.AlignCenter)
