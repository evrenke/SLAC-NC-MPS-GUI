from os import path
from logging import getLogger
from glob import glob
# from dbinteraction.configDB.fault_device_type import Fault_Device_Type as FDT
from dbinteraction.configDB.link_node_fault import Link_Node_Fault as LNF
from dbinteraction.configDB.epics_fault import Epics_Fault as EF
from dbinteraction.configDB.link_node_channel_fault import Link_Node_Channel_Fault as LNCF
from dbinteraction.configDB.link_processor_fault import Link_Processor_Fault as LPF
from dbinteraction.configDB.zlinknode import ZlinkNode as zln
from dbinteraction.mps_config import MPSConfig
from models.prepped_fault import PreppedFault


class ALLFaultsModel:
    """
    author: Evren Keskin
    ===================================================================
    ConfigDB accesses the config database to get fault data
    the fault data also allows for the related PV to be generated to access fault data
    ===================================================================
    """
    def __init__(self, accel_type: str, filename=None):
        """
        Establish logger and establish connection to mps_database.
        1) connect to the db file
        2) create dictionary of prepped faults
        """
        logger = getLogger(__name__)

        if filename and path.exists(filename):
            self.filename = filename
        else:
            if filename:
                logger.error("File does not exist. Using default .db file.")
            self.filename = self.set_filename(accel_type)

        self.configurator = MPSConfig(self.filename)

        self.set_all_node_fault_attributes()

    def set_filename(self, accel_type):
        """Finds default database filename."""
        if accel_type == 'LCLS':
            return self.set_LCLS_filename()
        else:  # FACET
            return self.set_FACET_filename()

    def set_LCLS_filename(self):
        print('redefining path to default LCLS faults file')
        phys_top = path.expandvars("$EPICS_IOC_TOP")
        versionFile = phys_top + "/MpsConfiguration/current/database/current"
        with open(versionFile) as f:
            first_line = f.readline()

        first_line = first_line.strip()
        filename = glob(phys_top + f'/MpsConfiguration/current/database/{first_line}/mpsdb.sqlite3')[0]
        return filename

    def set_FACET_filename(self):
        print('redefining path to default FACET faults file')
        phys_top = path.expandvars("$EPICS_IOC_TOP")
        versionFile = phys_top + "/MpsConfiguration-FACET/current/database/current"
        with open(versionFile) as f:
            first_line = f.readline()

        first_line = first_line.strip()
        filename = glob(phys_top + f'/MpsConfiguration-FACET/current/database/{first_line}/mpsdb.sqlite3')[0]
        return filename

    def set_all_node_fault_attributes(self):
        """
        Set attributes for all faults in one function
        Each query sets specific attributes alongside common ones, adding to the final list
        """
        query_results = []
        with self.configurator.Session() as session:
            ef_query_results = session.query(EF.area, EF.description, EF.device_name,
                                             EF.fault_name, EF.fault_number, EF.faulted_state_name,
                                             EF.is_autorecoverable, EF.ok_state_name, EF.pv_area,
                                             EF.pv_attribute, EF.pv_device_type, EF.pv_position,
                                             EF.input_pv, EF.position_x,
                                             EF.position_y, EF.position_z).all()

        for ef in ef_query_results:
            fault = PreppedFault()
            fault.device_name = ef.device_name
            fault.fault_name = ef.fault_name
            fault.fault_number = ef.fault_number
            fault.pv = (f"{ef.pv_device_type}:{ef.pv_area}:{ef.pv_position}:{ef.pv_attribute}")
            fault.ok_state_name = ef.ok_state_name
            fault.faulted_state_name = ef.faulted_state_name
            fault.is_autorecoverable = ef.is_autorecoverable
            fault.description = ef.description
            fault.area = ef.area
            fault.input_pv = ef.input_pv
            fault.position_x = ef.position_x
            fault.position_y = ef.position_y
            fault.position_z = ef.position_z
            fault.fault_type = EF

            query_results.append(fault)

        with self.configurator.Session() as session:
            lnf_query_results = session.query(LNF.area, LNF.description, LNF.device_name,
                                              LNF.fault_name, LNF.fault_number, LNF.faulted_state_name,
                                              LNF.is_autorecoverable, LNF.ok_state_name, LNF.pv_area,
                                              LNF.pv_attribute, LNF.pv_device_type, LNF.pv_position,
                                              LNF.link_node_id, zln.ZHOSTNAME).where(
                LNF.link_node_id == zln.ZLINKNODEID).all()

        for lnf in lnf_query_results:
            fault = PreppedFault()
            fault.device_name = lnf.device_name
            fault.fault_name = lnf.fault_name
            fault.fault_number = lnf.fault_number
            fault.pv = (f"{lnf.pv_device_type}:{lnf.pv_area}:{lnf.pv_position}:{lnf.pv_attribute}_LN{lnf.link_node_id}")
            fault.ok_state_name = lnf.ok_state_name
            fault.faulted_state_name = lnf.faulted_state_name
            fault.is_autorecoverable = lnf.is_autorecoverable
            fault.description = lnf.description
            fault.area = lnf.area
            fault.link_node_id = lnf.link_node_id
            fault.hostname = lnf.ZHOSTNAME
            fault.fault_type = LNF

            query_results.append(fault)

        with self.configurator.Session() as session:
            lncf_query_results = session.query(LNCF.area, LNCF.description, LNCF.device_name,
                                               LNCF.fault_name, LNCF.fault_number,
                                               LNCF.faulted_state_name,
                                               LNCF.is_autorecoverable, LNCF.ok_state_name, LNCF.pv_area,
                                               LNCF.pv_attribute, LNCF.pv_device_type, LNCF.pv_position,
                                               LNCF.cable, LNCF.card, LNCF.channel,
                                               LNCF.debounce_time, LNCF.is_deadman, LNCF.link_node_id,
                                               LNCF.position_x, LNCF.position_y, LNCF.position_z).all()

        for lncf in lncf_query_results:
            fault = PreppedFault()
            fault.device_name = lncf.device_name
            fault.fault_name = lncf.fault_name
            fault.fault_number = lncf.fault_number
            fault.pv = (f"{lncf.pv_device_type}:{lncf.pv_area}:{lncf.pv_position}:{lncf.pv_attribute}")
            fault.ok_state_name = lncf.ok_state_name
            fault.faulted_state_name = lncf.faulted_state_name
            fault.is_autorecoverable = lncf.is_autorecoverable
            fault.description = lncf.description
            fault.area = lncf.area
            fault.cable = lncf.cable
            fault.card = lncf.card
            fault.channel = lncf.channel
            fault.debounce_time = lncf.debounce_time
            fault.is_deadman = lncf.is_deadman
            fault.link_node_id = lncf.link_node_id
            fault.position_x = lncf.position_x
            fault.position_y = lncf.position_y
            fault.position_z = lncf.position_z
            fault.fault_type = LNCF

            query_results.append(fault)

        with self.configurator.Session() as session:
            lpf_query_results = session.query(LPF.area, LPF.description, LPF.device_name,
                                              LPF.fault_name, LPF.fault_number, LPF.faulted_state_name,
                                              LPF.is_autorecoverable, LPF.ok_state_name, LPF.pv_area,
                                              LPF.pv_attribute, LPF.pv_device_type, LPF.pv_position,
                                              LPF.position_x, LPF.position_y, LPF.position_z).all()

        for lpf in lpf_query_results:
            fault = PreppedFault()
            fault.device_name = lpf.device_name
            fault.fault_name = lpf.fault_name
            fault.fault_number = lpf.fault_number
            fault.pv = (f"{lpf.pv_device_type}:{lpf.pv_area}:{lpf.pv_position}:{lpf.pv_attribute}")
            fault.ok_state_name = lpf.ok_state_name
            fault.faulted_state_name = lpf.faulted_state_name
            fault.is_autorecoverable = lpf.is_autorecoverable
            fault.description = lpf.description
            fault.area = lpf.area
            fault.position_x = lpf.position_x
            fault.position_y = lpf.position_y
            fault.position_z = lpf.position_z
            fault.fault_type = LPF

            query_results.append(fault)

        self.nums_to_faults = {fault.fault_number: fault for fault in query_results}

    def get_fault_by_num(self, num=None):
        """
        Get a fault from the fault list using its fault number
        """
        if self.nums_to_faults is None:
            return None
        return self.nums_to_faults[num]

    def get_fault_by_signal(self, signalName=None):
        """
        Get a fault from the fault list using its 'signal name', a combination of the device and fault names
        """
        for fault_num in self.nums_to_faults:
            if (signalName == self.nums_to_faults[fault_num].device_name
                    + '_' + self.nums_to_faults[fault_num].fault_name):
                return self.nums_to_faults[fault_num]

        return None
