from sqlalchemy import Column, Integer, String
from .models_init import Base


class Macro_State(Base):
    """
    author: Evren Keskin
    Macro_State class (macro_state table)

    Describe a Macro_State, which is composed of the
    macro foreign key, state number, name of the state,
    is default flag,
    solution to the macro fault
    and the names and enumerations of the rates of the 7 possible LCLS devices

    Properties:
    macro_fk: macro device foreign key, referring to primary keys in Macro table
    state_number: a number representing the given macro state
    name: a name for the given macro state
    rate_name_gunl: rate name of Gun Linac device
    rate_name_ms: rate name of Mechanical Shutter device
    rate_name_bykik: rate name of the BYKIK HXR device
    rate_name_lhs: rate name of the Laser Heater device
    rate_name_gunh: rate name of the Gun HXR device
    rate_name_guns: rate name of the Gun SXR device
    rate_name_bykiks: rate name of the BYKIK SXR device
    rate_enum_gunl: rate enumeration of Gun Linac device
    rate_enum_ms: rate enumeration of Mechanical Shutter device
    rate_enum_bykik: rate enumeration of the BYKIK HXR device
    rate_enum_lhs: rate enumeration of the Laser Heater device
    rate_enum_gunh: rate enumeration of the Gun HXR device
    rate_enum_guns: rate enumeration of the Gun SXR device
    rate_enum_bykiks: rate enumeration of the BYKIK SXR device
    is_default: flag for if the state is default for the device or not
    solution: string description of fault solution for the macro state

    Relationships:
    --- None

    """
    __tablename__ = 'macro_state'

    macro_fk = Column('macro_fk', Integer)
    state_number = Column('state_number', Integer, primary_key=True)
    state_name = Column('name', String)

    rate_name_gunl = Column('rate_name_gunl', String)
    rate_name_ms = Column('rate_name_ms', String)
    rate_name_bykik = Column('rate_name_bykik', String)
    rate_name_lhs = Column('rate_name_lhs', String)
    rate_name_gunh = Column('rate_name_gunh', String)
    rate_name_guns = Column('rate_name_guns', String)
    rate_name_bykiks = Column('rate_name_bykiks', String)

    rate_enum_gunl = Column('rate_enum_gunl', Integer)
    rate_enum_ms = Column('rate_enum_ms', Integer)
    rate_enum_bykik = Column('rate_enum_bykik', Integer)
    rate_enum_lhs = Column('rate_enum_lhs', Integer)
    rate_enum_gunh = Column('rate_enum_gunh', Integer)
    rate_enum_guns = Column('rate_enum_guns', Integer)
    rate_enum_bykiks = Column('rate_enum_bykiks', Integer)

    is_default = Column('is_default', Integer)
    solution = Column('solution', String)
