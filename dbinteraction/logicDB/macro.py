from sqlalchemy import Column, Integer, String
from .models_init import Base


class Macro(Base):
    """
    author: Evren Keskin
    Macro class (macro table)

    Describe a Macro, which is composed of the
    primary key, macro number, name of the macro
    is active flag and is code flag
    code field if it has code
    and description of the macro

    Properties:
    pk: primary key for this macro, used by many other database tables
    macro_number: the number for this particular macro, the primary key for this table
    name: string name for the macro
    is_active: flag for is active or not
    is_code: flag for if this macro is a code or not
    code: if this macro is a code, holds an integer code field
    description: string description of this macro

    Relationships:
    --- None

    """
    __tablename__ = 'macro'

    pk = Column('pk', Integer)
    macro_number = Column('macro_number', Integer, primary_key=True)
    name = Column('name', String)
    is_active = Column('is_active', Integer)
    is_code = Column('is_code', Integer)
    code = Column('code', String)
    description = Column('description', String)
