from sqlalchemy import create_engine, exc
from sqlalchemy import Table, Column, String, MetaData
from sqlalchemy import BigInteger
from sqlalchemy.dialects import postgresql, mysql, sqlite
from dbinteraction.recentStatesDB.recent_state import Recent_State
from mps_constants import RECENT_FAULTS_MAX

# https://www.tutorialspoint.com/sqlalchemy/sqlalchemy_core_creating_table.htm


def do_single_insert(session, date_param, macro_name_param, state_name_param,
                     min_rate_param='--', rate_gunl_param='--',
                     rate_ms_param='--', rate_bykik_param='--', rate_lhs_param='--',
                     rate_gunh_param='--', rate_guns_param='--', rate_bykiks_param='--'):
    # print('inserting 1 item:', date_param)
    # configurator = MPSConfig(recent_sqlite_file)

    numberOfThings = session.query(Recent_State).count()
    if numberOfThings >= RECENT_FAULTS_MAX:
        # print('removing 1 oldest item')
        # DELETE FROM Recent_State WHERE id IN (SELECT id FROM Recent_State ORDER BY id LIMIT 1)
        first_item = session.query(Recent_State).order_by(Recent_State.id.asc()).first()
        session.delete(first_item)

    rs = Recent_State(date=date_param, macro_name=macro_name_param, state_name=state_name_param,
                      min_rate=min_rate_param, rate_gunl=rate_gunl_param, rate_ms=rate_ms_param,
                      rate_bykik=rate_bykik_param, rate_lhs=rate_lhs_param, rate_gunh=rate_gunh_param,
                      rate_guns=rate_guns_param, rate_bykiks=rate_bykiks_param)

    session.add(rs)
    session.commit()
    session.close()

    # print('new length:', configurator.session.query(Recent_State.id).count())


def do_select(session):

    # SELECT id, date, macro_name, state_name, min_rate, \
    # rate_gunl, rate_ms, rate_bykik, rate_lhs, rate_gunh, rate_guns, rate_bykiks \
    # FROM recent_states \
    # ORDER BY date ;

    results = session.query(Recent_State.id, Recent_State.date, Recent_State.macro_name,
                            Recent_State.state_name, Recent_State.min_rate, Recent_State.rate_gunl,
                            Recent_State.rate_ms, Recent_State.rate_bykik,
                            Recent_State.rate_lhs, Recent_State.rate_gunh,
                            Recent_State.rate_guns, Recent_State.rate_bykiks).order_by(
                                Recent_State.date).all()
    notsqliterelatedresults = []  # convert results to a regular list in python
    for item in results:
        notsqliterelatedresults.append(item)

    return notsqliterelatedresults


def create_db_if_not_exists(recent_sqlite_file):
    meta = MetaData()
    # create database if not exists
    try:
        engine = create_engine(f"sqlite:///{recent_sqlite_file}", echo=True)
        # Attempt to connect to the database
        with engine.connect() as conn:
            print(f'Database {recent_sqlite_file} already exists.')
    except exc.OperationalError:
        # raise Exception
        print(f'Database {recent_sqlite_file} does not exist. Creating now.')
        engine = create_engine(f"sqlite:///{recent_sqlite_file}", echo=True)  # using postgres db to connect
        # Attempt to connect to the database
        with engine.connect() as conn:
            conn.execute("commit")
            conn.execute(f'CREATE DATABASE {recent_sqlite_file};')

    create_table_in_db(meta)

    meta.create_all(engine)


def create_table_in_db(meta):
    BigIntegerType = BigInteger()
    BigIntegerType = BigIntegerType.with_variant(postgresql.BIGINT(), 'postgresql')
    BigIntegerType = BigIntegerType.with_variant(mysql.BIGINT(), 'mysql')
    BigIntegerType = BigIntegerType.with_variant(sqlite.INTEGER(), 'sqlite')
    recent_state = Table(
        'recent_state', meta,
        Column('id', BigIntegerType, primary_key=True, autoincrement=True),
        Column('date', String),
        Column('macro_name', String),
        Column('state_name', String),
        Column('min_rate', String),
        Column('rate_gunl', String),
        Column('rate_ms', String),
        Column('rate_bykik', String),
        Column('rate_lhs', String),
        Column('rate_gunh', String),
        Column('rate_guns', String),
        Column('rate_bykiks', String),
    )

    return recent_state
