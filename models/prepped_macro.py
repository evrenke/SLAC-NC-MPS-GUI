from .prepped_macro_state import PreppedMacroState


class PreppedMacro():
    """
    author: Evren Keskin
    ===================================================================
    This class represents a 'Macro': a real device, a virtual/code device, or an ignoring condition setter
    with relation to its macro, macro state, and ignored added
    A PreppedMacro represents information about a device, its possible states
    its current state, its current faults, if it is ignored or not, and possibly its date
    ===================================================================
    """

    UNDEFINED_RATE_VAL = 10

    def __init__(self):
        # macro attributes:
        self.macro_number = None
        self.macro_name = None
        self.is_code = None
        self.code = None
        # macro state attributes:
        self.macro_states = []
        self.current_index = None
        self.has_special_error_state = False
        self.special_state = None
        # is ignored flag from ignored macro list:
        self.is_ignoring = None
        self.ignored_macros = []
        self.min_rate_from_ignored = 11  # 'Ignore Logic' by default
        # faults list:
        self.faults = []
        # recent fault attributes:
        self.date = None

    def add_fault(self, new_fault):
        self.faults.append(new_fault)
        new_fault.relatedPreppedMacro = self

    def add_macro_state(self, new_state):
        self.macro_states.append(new_state)
        if len(self.macro_states) == 1:
            self.current_index = 0

        self.macro_states.sort(key=lambda ms: ms.state_number)

    def get_current_state(self):
        if self.has_special_error_state:
            return self.special_state
        return self.macro_states[self.current_index]

    def set_current_state(self, new_state_number):
        """
        Sets the macro's new current state. It can also set special error states
        special number -53, -54, -55, -56 represents N/A, Ignored, Active, and Inactive states for a device
        """
        if not self.has_special_error_state and (
                new_state_number == -53 or
                new_state_number == -54 or
                new_state_number == -55 or
                new_state_number == -56):

            macroState = PreppedMacroState()
            macroState.relatedPreppedMacro = self
            macroState.state_number = new_state_number
            macroState.rate_enums = [self.UNDEFINED_RATE_VAL,
                                     self.UNDEFINED_RATE_VAL,
                                     self.UNDEFINED_RATE_VAL,
                                     self.UNDEFINED_RATE_VAL,
                                     self.UNDEFINED_RATE_VAL,
                                     self.UNDEFINED_RATE_VAL,
                                     self.UNDEFINED_RATE_VAL]

            macroState.is_ignored = False

            if new_state_number == -53:
                macroState.state_name = "N/A"
            elif new_state_number == -54:
                macroState.state_name = "Ignored"
            elif new_state_number == -55:
                macroState.state_name = "Active"
            elif new_state_number == -56:
                macroState.state_name = "Inactive"
            else:
                macroState.state_name = "N/A"

            self.special_state = macroState

            # THE IMPORTANT LINE THAT THIS FUNCTION IS CALLED FOR: Sets what will be returned for current state
            # signifies that there is a special error macro state for this device
            self.has_special_error_state = True
            return

        isIgnored = new_state_number < 0

        # By this point of the code, we have determined that the current macro state is not a designated error state
        # So we can pick an actual macro state based on the defined macro states of this device

        if new_state_number < 0:  # negative number state represents a positive number state that is ignored
            new_state_number = new_state_number & 0x7f

        for state in self.macro_states:
            if state.state_number == new_state_number:
                self.has_special_error_state = False
                # THE IMPORTANT LINE THAT THIS FUNCTION IS CALLED FOR: Sets what will be returned for current state
                self.current_index = self.macro_states.index(state)
                state.is_ignored = isIgnored
                break

    def set_ignored_macros(self, ignored_macros):
        """
        Takes a given list of macros which this one will be ignoring
        If this is used, it means that this macro is a condition macro
        If nothing is passed in, then the ignored macros list is reset
        """
        if not self.is_ignoring:
            return

        self.ignored_macros = []
        if ignored_macros is None or ignored_macros == []:
            self.min_rate_from_ignored = 11
            self.ignored_macros = []
            return

        for macro in ignored_macros:
            self.ignored_macros.append(macro)

    def get_min_rate_from_ignored(self):
        """
        This is used to get the minimum rate of the ignored macros
        This is only called for condition macros
        By default, it is set to 'Ignore Logic'
        Otherwise, it gets the minimum of the minimum rates of the associated macros
        """
        if not self.is_ignoring:
            return PreppedMacroState.get_enum_to_val(11)  # Ignore Logic default for not having ignored macros

        min = 11
        for macro in self.ignored_macros:
            if min > macro.get_current_state().get_min_rate():
                min = macro.get_current_state().get_min_rate()
        self.min_rate_from_ignored = min
        return PreppedMacroState.get_enum_to_val(self.min_rate_from_ignored)

    def get_state_by_state_number(self, state_num):
        """
        This is used to get states of unknown indexes by that states number
        rather than an index internal to this macro's list
        Mainly used for recent faults getting states
        """
        if state_num == -53 or state_num == -54 or state_num == -55 or state_num == -56:
            macroState = PreppedMacroState()
            macroState.relatedPreppedMacro = self
            macroState.state_number = state_num
            macroState.rate_enums = [self.UNDEFINED_RATE_VAL,
                                     self.UNDEFINED_RATE_VAL,
                                     self.UNDEFINED_RATE_VAL,
                                     self.UNDEFINED_RATE_VAL,
                                     self.UNDEFINED_RATE_VAL,
                                     self.UNDEFINED_RATE_VAL,
                                     self.UNDEFINED_RATE_VAL]

            macroState.is_ignored = True

            if state_num == -53:
                macroState.state_name = "N/A"
            elif state_num == -54:
                macroState.state_name = "Ignored"
            elif state_num == -55:
                macroState.state_name = "Active"
            elif state_num == -56:
                macroState.state_name = "Inactive"
            else:
                macroState.state_name = "N/A"

            return macroState

        for state in self.macro_states:
            if state.state_number == state_num or state.state_number == (state_num & 0x7f):
                return state

        return None
