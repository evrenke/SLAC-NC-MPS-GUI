from sqlalchemy import Column, Integer
from .models_init import Base


class ZIgnoreMacro(Base):
    """
    author: Evren Keskin
    ZIgnoreMacro class (zignoremacro table)

    Describe a ZIgnoreMacro, which is composed of the
    primary key, and the macro key for the ignored macro

    Properties:
    z_pk: primary key for this ignored entry
    zmacro: the related number for the ignored macro

    Relationships:
    --- None

    """
    __tablename__ = 'zignoremacro'

    z_pk = Column('pk', Integer, primary_key=True)
    zmacro = Column('zmacro', Integer)
