from dbinteraction.historyDB.oracle_utilities import (get_beam_destinations, get_beam_rates,
                                                      get_bypass_times, get_bypass_values, get_faults)
from models.prepped_message import PreppedMessage
import time
from mps_constants import FROM_1970_TO_1990_IN_SECONDS


class AllMessagesModel:
    """
    author: Evren Keskin
    ===================================================================
    ConfigDB accesses the config database to get fault data
    the fault data also allows for the related PV to be generated to access fault data
    ===================================================================
    Overall steps when running
    1) Create a list of messages with oracle queries
    2) Begin listening for new messages, updating message list continuously
    3) Create option for getting a specific time range of messages
    """
    def __init__(self, wallet):
        self.liveMessages = []
        self.interactiveMessages = []
        self.check_end_time = int(time.time() - FROM_1970_TO_1990_IN_SECONDS)
        self.walletName = wallet
        # 8 hours ago
        self.check_start_time = self.check_end_time - 3600 * 8

        # Initialize new messages with the starting interval from above:
        newMessages = self.get_messages_in_interval(self.check_start_time, self.check_end_time)
        for message in newMessages:
            self.liveMessages.append(message)

    def get_messages_in_interval(self, start, end):
        messages = []
        beam_destination_messages = get_beam_destinations(start, 0, end, 0, self.walletName)

        if not (beam_destination_messages == [] or beam_destination_messages is None):
            for bdm in beam_destination_messages:
                newMessage = PreppedMessage()
                newMessage.set_beam_dest_message(bdm.prev_name, bdm.curr_name, bdm.sec, bdm.nsec)
                messages.append(newMessage)

        beam_rates_messages = get_beam_rates(start, 0, end, 0, self.walletName)

        if not (beam_rates_messages == [] or beam_rates_messages is None):
            for brm in beam_rates_messages:
                newMessage = PreppedMessage()
                newMessage.set_beam_rate_message(brm[2], brm[3], brm[4], brm[0], brm[1])
                messages.append(newMessage)

        bypass_time_messages = get_bypass_times(start, 0, end, 0, self.walletName)

        if not (bypass_time_messages == [] or bypass_time_messages is None):
            for btm in bypass_time_messages:
                newMessage = PreppedMessage()
                newMessage.set_bypass_time_message(btm[2], btm[3], btm[4], btm[0], btm[1])
                messages.append(newMessage)

        bypass_value_messages = get_bypass_values(start, 0, end, 0, self.walletName)

        if not (bypass_value_messages == [] or bypass_value_messages is None):
            for bvm in bypass_value_messages:
                newMessage = PreppedMessage()
                newMessage.set_bypass_value_message(bvm[2], bvm[3], btm[4], bvm[5], bvm[0], bvm[1])
                messages.append(newMessage)

        faults_messages = get_faults(start, 0, end, 0, self.walletName)

        if not (faults_messages == [] or faults_messages is None):
            for fm in faults_messages:
                newMessage = PreppedMessage()
                newMessage.set_fault_message(fm[2], fm[3], fm[4], fm[5], fm[0], fm[1])
                messages.append(newMessage)

        messages.sort()

        return messages

    def update_live_messages(self):
        self.check_start_time = self.check_end_time
        self.check_end_time = int(time.time() - FROM_1970_TO_1990_IN_SECONDS)
        newMessages = self.get_messages_in_interval(self.check_start_time, self.check_end_time)
        for message in newMessages:
            self.liveMessages.append(message)

    def update_interval_messages(self, startSeconds, endSeconds):
        self.interactiveMessages = self.get_messages_in_interval(startSeconds, endSeconds)
