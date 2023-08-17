"""Utility functions for Oracle.

This file contains functions for retrieving data from Oracle
specifically the elements database, magnet polynomial
database, additional data, and SCORE.

Copied from /afs/slac/g/lcls/tools/script/
MagnetAutoCheckout/helpers/mgnt_oracle_utilities.py

Modified for History DB use
"""

import os

import cx_Oracle


def connect(wallet, user):
    """Connects to Oracle.

    Args:
        wallet (str): The Oracle wallet, which contains credentials
        user (str): The username of the Oracle database

    Returns:
        A connection object on which one can execute Oracle queries.
    """
    # If on dev, use afs directories
    wallet_dir = '/usr/local/lcls/tools/oracle/wallets'
    if not os.path.isdir(wallet_dir):
        wallet_dir = '/afs/slac/g/lcls/tools/oracle/wallets'
        os.environ['ORACLE_HOME'] = '/afs/slac/g/lcls/package/oracle/product/11.2.0.4/linux-x86_64'

    else:
        os.environ['ORACLE_HOME'] = '/usr/local/lcls/package/oracle/product/11.2.0.4/linux-x86_64'

    os.environ['TNS_ADMIN'] = os.path.join(wallet_dir, wallet)
    os.environ['TWO_TASK'] = user
    con = cx_Oracle.connect('/@' + user)
    return con


def run_query(wallet, user, query):
    """Executes a query on Oracle.

    Args:
        wallet (str): The Oracle wallet, which contains credentials
        user (str): The username of the Oracle database
        query (str): The SQL query.

    Returns:
        A list of the rows returned by Oracle. Each row is a tuple.

    """
    con = connect(wallet, user)
    cur = con.cursor()
    cur.execute(query)
    res = cur.fetchall()
    cur.close()
    con.close()
    return res


def get_beam_destinations(startSeconds, startNanos, endSeconds, endNanos, wallet):
    "Returns boolean of possible retrieved messages data for history"

    user = 'MCCQA'

    liketoken = '%_%'

    query = f'SELECT \
    bdest.timestamp_sec_past_epoch sec, \
    bdest.timestamp_nsec     nsec, \
    pdest.destination_name     prev_name, \
    cdest.destination_name     curr_name \
    FROM \
    beam_destination bdest LEFT OUTER JOIN \
    destination pdest ON bdest.prev_dest_destination_fk = pdest.id LEFT OUTER JOIN \
    destination cdest ON bdest.curr_dest_destination_fk = cdest.id \
    WHERE \
        (bdest.timestamp_sec_past_epoch > {startSeconds} OR \
        (bdest.timestamp_sec_past_epoch = {startSeconds} AND bdest.timestamp_nsec >= {startNanos})) \
        AND \
        (bdest.timestamp_sec_past_epoch < {endSeconds} OR \
        (bdest.timestamp_sec_past_epoch = {endSeconds} AND bdest.timestamp_nsec <= {endNanos})) \
        AND \
        pdest.destination_name LIKE \'{liketoken}\' \
        AND \
            cdest.destination_name LIKE \'{liketoken}\' \
    ORDER BY timestamp_sec_past_epoch DESC, timestamp_nsec DESC'

    return run_query(wallet, user, query)


def get_beam_rates(startSeconds, startNanos, endSeconds, endNanos, wallet):
    "Returns boolean of possible retrieved messages data for history"

    user = 'MCCQA'

    liketoken = '%_%'

    query = f'SELECT \
    brate.timestamp_sec_past_epoch sec, \
    brate.timestamp_nsec nsec, \
    device.device_name dev_name, \
    prate.rate_name prev_rate, \
    crate.rate_name curr_rate\
    FROM \
    beam_rate_after_device brate LEFT OUTER JOIN \
    rate_limiting_device device ON brate.mitigation_device_rld_fk = device.id LEFT OUTER JOIN \
    rate prate ON brate.prev_rate_rate_fk = prate.id LEFT OUTER JOIN \
    rate crate ON brate.curr_rate_rate_fk = crate.id \
    WHERE \
    ( \
        (brate.timestamp_sec_past_epoch > {startSeconds}) OR \
        ( \
            (brate.timestamp_sec_past_epoch = {startSeconds}) AND \
            (brate.timestamp_nsec >= {startNanos}) \
        ) \
    ) \
    AND \
    ( \
        (brate.timestamp_sec_past_epoch < {endSeconds}) OR \
        ( \
            (brate.timestamp_sec_past_epoch = {endSeconds}) AND \
            (brate.timestamp_nsec <= {endNanos}) \
        ) \
    ) \
    AND \
    prate.rate_name LIKE \'{liketoken}\' \
    ORDER BY timestamp_sec_past_epoch DESC, timestamp_nsec DESC'

    return run_query(wallet, user, query)


def get_bypass_times(startSeconds, startNanos, endSeconds, endNanos, wallet):
    "Returns boolean of possible retrieved messages data for history"

    user = 'MCCQA'

    liketoken = '%_%'

    query = f'SELECT timestamp_sec_past_epoch, timestamp_nsec, \
    device_name,  fault_name, bypass_time_in_seconds \
    FROM bypass_time \
    WHERE (timestamp_sec_past_epoch > {startSeconds} OR \
    (timestamp_sec_past_epoch = {startSeconds} AND timestamp_nsec >= {startNanos})) \
    AND \
    (timestamp_sec_past_epoch < {endSeconds} OR \
    (timestamp_sec_past_epoch = {endSeconds} AND timestamp_nsec <= {endNanos})) \
    AND \
    (device_name LIKE \'{liketoken}\' OR \
    fault_name LIKE \'{liketoken}\') \
    ORDER BY timestamp_sec_past_epoch DESC, timestamp_nsec DESC'

    return run_query(wallet, user, query)


def get_bypass_values(startSeconds, startNanos, endSeconds, endNanos, wallet):
    "Returns boolean of possible retrieved messages data for history"

    user = 'MCCQA'

    liketoken = '%_%'

    query = f'SELECT timestamp_sec_past_epoch, timestamp_nsec, \
    device_name,  fault_name, prev_value, curr_value \
    FROM bypass_value \
    WHERE (timestamp_sec_past_epoch > {startSeconds} OR \
    (timestamp_sec_past_epoch = {startSeconds} AND timestamp_nsec >= {startNanos})) \
    AND \
    (timestamp_sec_past_epoch < {endSeconds} OR \
    (timestamp_sec_past_epoch = {endSeconds} AND timestamp_nsec <= {endNanos})) \
    AND \
    (device_name LIKE \'{liketoken}\' OR \
    fault_name LIKE \'{liketoken}\') \
    ORDER BY timestamp_sec_past_epoch DESC, timestamp_nsec DESC'

    return run_query(wallet, user, query)


def get_faults(startSeconds, startNanos, endSeconds, endNanos, wallet):
    "Returns boolean of possible retrieved messages data for history"

    user = 'MCCQA'

    liketoken = '%_%'

    query = f'SELECT timestamp_sec_past_epoch, timestamp_nsec, \
    device_name,  fault_name, prev_state, curr_state \
    FROM fault \
    WHERE (timestamp_sec_past_epoch > {startSeconds} OR \
    (timestamp_sec_past_epoch = {startSeconds} AND timestamp_nsec >= {startNanos})) \
    AND \
    (timestamp_sec_past_epoch < {endSeconds} OR \
    (timestamp_sec_past_epoch = {endSeconds} AND timestamp_nsec <= {endNanos})) \
    AND \
    (device_name LIKE \'{liketoken}\' OR \
    fault_name LIKE \'{liketoken}\') \
    ORDER BY timestamp_sec_past_epoch DESC, timestamp_nsec DESC'

    return run_query(wallet, user, query)
