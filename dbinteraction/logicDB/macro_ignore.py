from sqlalchemy import Column, Integer
from .models_init import Base


class Macro_Ignore(Base):
    """
    author: Evren Keskin
    Macro_Ignore class (macro_ignore table)

    Describe a Macro_Ignore, which is composed of the
    macro foreign key, and the ignored when macro foreign key

    Properties:
    macro_fk: macro device foreign key, referring to primary keys in Macro table
    ignored when macro foreign key: the foreign key for the ignored macro, referring to zignoremacro table

    Relationships:
    --- None

    """
    __tablename__ = 'macro_ignore'

    macro_fk = Column('macro_fk', Integer, primary_key=True)
    ignored_when_macro_fk = Column('ignored_when_macro_fk', Integer)
