from sqlalchemy import Column, String
from .models_init import Base
from sqlalchemy import BigInteger
from sqlalchemy.dialects import postgresql, mysql, sqlite


class Recent_State(Base):
    """
    author: Evren Keskin
    Recent_State class (recent_state table)

    Describe a Recent_State, which is composed of the
    id, date, name of the macro, name of the state,
    min rate as string
    and the rates as strings of the 7 possible LCLS devices

    Properties:
    id: autoincrementing numeric ID for all items
    date: a string representing what date and time this recent fault happened
    macro_name: a name for the given macro
    state_name: a name for the given macro state
    min_rate: min of all the rates as a string
    rate_enum_gunl: rate as a string of Gun Linac device
    rate_enum_ms: rate as a string of Mechanical Shutter device
    rate_enum_bykik: rate as a string of the BYKIK HXR device
    rate_enum_lhs: rate as a string of the Laser Heater device
    rate_enum_gunh: rate as a string of the Gun HXR device
    rate_enum_guns: rate as a string of the Gun SXR device
    rate_enum_bykiks: rate as a string of the BYKIK SXR device


    Relationships:
    --- None

    """
    __tablename__ = 'recent_state'

    # SQLAlchemy does not map BigInt to Int by default on the sqlite dialect.
    # It should, but it doesnt.
    BigIntegerType = BigInteger()
    BigIntegerType = BigIntegerType.with_variant(postgresql.BIGINT(), 'postgresql')
    BigIntegerType = BigIntegerType.with_variant(mysql.BIGINT(), 'mysql')
    BigIntegerType = BigIntegerType.with_variant(sqlite.INTEGER(), 'sqlite')

    id = Column('id', BigIntegerType, primary_key=True, autoincrement=True)
    date = Column('date', String)
    macro_name = Column('macro_name', String)
    state_name = Column('state_name', String)

    min_rate = Column('min_rate', String)
    rate_gunl = Column('rate_gunl', String)
    rate_ms = Column('rate_ms', String)
    rate_bykik = Column('rate_bykik', String)
    rate_lhs = Column('rate_lhs', String)
    rate_gunh = Column('rate_gunh', String)
    rate_guns = Column('rate_guns', String)
    rate_bykiks = Column('rate_bykiks', String)
