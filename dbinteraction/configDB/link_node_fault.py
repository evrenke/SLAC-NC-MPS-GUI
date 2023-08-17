from sqlalchemy import Column, Integer, String
from .models_init import Base


class Link_Node_Fault(Base):
    """
    author: Evren Keskin
    Link_Node_Fault class (link_node_fault table)

    Describe a Link Node Fault , which is composed of the device name,
    fault name, fault id, fault number,
    processing variable(pv) device type, pv area, pv position, pv attribute,
    ok state name, faulted state name,
    is autorecoverable,
    description of the fault and area,
    and specific to the link node fault:
    the link node id

    Properties:
    device_name: string name of the device with the epics fault
    fault_name: string name of the epics fault of the device
    fault_id: fault identifying number, used in many database tables
    fault_number:  a number for the fault, (not id), used to enumerate
    the faults in configuration
    pv_device_type: the device type used to set the processing variable
    pv_area: the device area/category used to set the processing variable
    pv_position: the device position used to set the processing variable
    pv_attribute: the device attribute used to set the processing variable
    ok_state_name: string for the fixed state of the device
    faulted_state_name: string for the faulted state of the device
    is_autorecoverable: an integer as a bool, used to describe if
    the fault can be fixed with autorecovery in the device
    description: string description of the fault of the device
    area: the area/category of the device with the fault

    ## LINK NODE FAULT SPECIFIC:
    link_node_id: id of the link node on the ZLinkNode table

    Relationships:
    --- None

    """
    __tablename__ = 'link_node_fault'

    device_name = Column('device_name', String)
    fault_name = Column('fault_name', String)
    fault_id = Column("fault_id", Integer, primary_key=True)
    fault_number = Column('fault_number')
    pv_device_type = Column("pv_device_type", String)
    pv_area = Column('pv_area', String)
    pv_position = Column('pv_position', String)
    pv_attribute = Column('pv_attribute', String)
    ok_state_name = Column('ok_state_name', String)
    faulted_state_name = Column('faulted_state_name', String)
    is_autorecoverable = Column('is_autorecoverable', Integer)
    description = Column('description', String)
    area = Column('area', String)
    # link node fault specific attribute:
    link_node_id = Column('link_node_id', Integer)
