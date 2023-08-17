
class PreppedMacroState():
    """
    author: Evren Keskin
    ===================================================================
    This class represents a Macro State loaded with relevant information
    It holds a list of rates for the state itself, and holds the state name and number
    The number of the state represents its index position in the truth table of a macro
    (if its not a code macro)
    ===================================================================
    """
    def __init__(self):
        self.state_number = None
        self.state_name = None
        self.rate_enums = []
        self.relatedPreppedMacro = None
        self.is_ignored = None

    def get_enum_to_val(enum):
        """
        Converts an int enumeration into the value it represents on the tables
        """
        if enum == 0:
            return 'Invalid'
        elif enum == 1:
            return '0 Hz'
        elif enum == 2:
            return 'Single Shot'
        elif enum == 3:
            return 'Burst Mode'
        elif enum == 4:
            return '1 Hz'
        elif enum == 5:
            return '10 Hz'
        elif enum == 6:
            return '30 Hz'
        elif enum == 7:
            return '60 Hz'
        elif enum == 8:
            return '120 Hz'
        elif enum == 9:
            return 'Unknown'
        elif enum == -1 or enum == 10:
            return '--'
        elif enum == 11:
            return 'Ignore Logic'

    def get_val_to_enum(value):
        """
        Converts a given rate from the table string value into the enumeration used for comparisons
        """
        if value == 'Invalid':
            return 0
        elif value == '0 Hz':
            return 1
        elif value == 'Single Shot':
            return 2
        elif value == 'Burst Mode':
            return 3
        elif value == '1 Hz':
            return 4
        elif value == '10 Hz':
            return 5
        elif value == '30 Hz':
            return 6
        elif value == '60 Hz':
            return 7
        elif value == '120 Hz':
            return 8
        elif value == 'Unknown':
            return 9
        elif value == '--':
            return 10
        elif value == 'Ignore Logic':
            return 11

    def get_min_rate(self):
        """
        Gets the minimum rate based on the 7 rates of LCLS macros
        Could be Ignore Logic if all 7 rates are none
        """
        min = None
        for rate in self.rate_enums:
            if min is None or min > rate:
                min = rate

        if min is None:
            min = 11  # Ignore Logic
        return min
