
class PreppedMessage():
    """
    author: Evren Keskin
    ===================================================================
    This class represents any of the 5 LCLS message types that can be loaded with information
    The first half of its attributes are common to all messages
    but the second half is specific fault message getters
    ===================================================================
    """
    def __init__(self):
        # Common attributes of all messages
        self.message = None
        self.message_type = None
        self.nanos = None
        self.seconds_from_1990 = None
        """ The oracle database of messages uses 01/01/1990 instead of the common 01/01/1970 as time zero."""

    def get_message(self):
        return self.message

    def get_seconds(self):
        return self.seconds_from_1990

    def get_nanos(self):
        return self.nanos

    def set_time(self, seconds, nanos):
        self.seconds_from_1990 = int(seconds)
        self.nanos = int(nanos)

    def set_beam_dest_message(self, previousDestination, currentDestination, seconds, nanos):
        self.set_time(seconds, nanos)
        self.message = f'Beam destination changed from {previousDestination} to {currentDestination}'
        self.message_type = 'BD'

    def set_beam_rate_message(self, deviceName, previousRate, newRate, seconds, nanos):
        self.set_time(seconds, nanos)
        self.message = f'Beam rate after {deviceName} changed from {previousRate} to {newRate}'
        self.message_type = 'BR'

    def set_bypass_time_message(self, deviceName, faultName, bypassTimeInSeconds, seconds, nanos):
        self.set_time(seconds, nanos)
        suffix = None
        if bypassTimeInSeconds > 0:
            suffix = f'is bypassed for {bypassTimeInSeconds} sec'
        else:
            suffix = 'bypass has cleared'
        self.message = f'{deviceName} {faultName} {suffix}'
        self.message_type = 'BT'

    def set_bypass_value_message(self, deviceName, faultName, oldValue, newValue, seconds, nanos):
        self.set_time(seconds, nanos)
        self.message = f'{deviceName} {faultName} changed from {oldValue} to {newValue}'
        self.message_type = 'BV'

    def set_fault_message(self, deviceName, faultName, oldState, newState, seconds, nanos):
        self.set_time(seconds, nanos)
        self.message = f'{deviceName} {faultName} changed from {oldState} to {newState}'
        self.message_type = 'F'

    # Not sure which one of these is used for sort comparisons
    # I just did all just for thoroughness

    def __eq__(self, obj):
        return (isinstance(obj, PreppedMessage) and obj.seconds_from_1990 == self.seconds_from_1990
                and obj.nanos == self.nanos
                and obj.message == self.message)

    def __lt__(self, obj):
        return (isinstance(obj, PreppedMessage) and obj.seconds_from_1990 < self.seconds_from_1990
                or (obj.seconds_from_1990 == self.seconds_from_1990 and obj.nanos < self.nanos)
                or (obj.seconds_from_1990 == self.seconds_from_1990 and
                    obj.nanos == self.nanos and obj.message < self.message))

    def __le__(self, obj):
        return (isinstance(obj, PreppedMessage) and obj.seconds_from_1990 <= self.seconds_from_1990
                or (obj.seconds_from_1990 == self.seconds_from_1990 and obj.nanos <= self.nanos)
                or (obj.seconds_from_1990 == self.seconds_from_1990 and
                    obj.nanos == self.nanos and obj.message <= self.message))

    def __gt__(self, obj):
        return not self.__le__(obj)

    def __ge__(self, obj):
        return not self.__lt__(obj)

    def __ne__(self, obj):
        return not self.__eq__(obj)
