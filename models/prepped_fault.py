
class PreppedFault():
    """
    author: Evren Keskin
    ===================================================================
    This class represents any of the 4 fault types that can be loaded with information
    The first half of its attributes are common to all faults
    but the second half is only specific to its fault type, and only relevent parameters are set
    ===================================================================
    """
    def __init__(self):
        # Common attributes of all faults
        self.device_name = None
        self.fault_name = None
        self.fault_number = None
        self.pv = None
        self.ok_state_name = None
        self.faulted_state_name = None
        self.is_autorecoverable = None
        self.description = None
        self.area = None
        self.fault_type = None
        self.relatedPreppedMacro = None

        # additional attributes for specific types of faults are added in MPSFaultModel

        self.position_x = None
        self.position_y = None
        self.position_z = None
        self.input_pv = None
        self.cable = None
        self.card = None
        self.channel = None
        self.is_deadman = None
        self.link_node_id = None
        self.hostname = None
        """ NEVER USED?????? WHY WAS THIS QUERIED IN JAVA"""
        self.debounce_time = None
