from sqlalchemy import Column, Integer, String
from .models_init import Base


class Macro_Device(Base):
    """
    author: Evren Keskin
    Macro_Device class (macro_device table)

    Describe a Macro_Device, which is composed of the macro foreign key,
    position, and device name

    Properties:
    macro_fk: macro device foreign key, referring to primary keys in Macro table
    position: the position of the macro device as an integer
    device_name: string name of the macro device

    Relationships:
    --- None

    """
    __tablename__ = 'macro_device'

    macro_fk = Column('macro_fk', Integer, primary_key=True)
    position = Column('position', Integer)
    device_name = Column('device_name', String)
