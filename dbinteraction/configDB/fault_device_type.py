from sqlalchemy import Column, Integer, String
from .models_init import Base


class Fault_Device_Type(Base):
    """
    author: Evren Keskin
    Fault_Device_Type class (fault_device_type table)

    A fault device type is a given faults type of device fault
    with a name and number

    Describe a digital Fault Device Type, which is composed of the fault id,
    the device type name, and integer for the device type

    Properties:
    fault_id: fault identifying number, used in many database tables
    device_type_name: string description of the type of the device
    device_type: an integer representing the type of the device

    Relationships:
    --- None

    """
    __tablename__ = 'fault_device_type'
    fault_id = Column("fault_id", Integer)
    device_type_name = Column("device_type_name", String, primary_key=True)
    device_type = Column("device_type", Integer)
