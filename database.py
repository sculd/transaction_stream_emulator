'''
The schema of the db is like this:
row key:<user id>#<timestamp>
column key:<dummy value>
value: <value>

The timestamp is placed after the user id so that a range search can be efficiently
done for particular user, which is the problem requirement.
The schema does not make particular use for the column key.
'''

from google.cloud import bigtable
import config

# I would hard-code these parameters
# in production these would be part of the config as well.
_TABLE_ID = 'dt'
COLUMN_FAMILY_ID_LIST = 'dcflist'
COLUMN_FAMILY_ID_BY_MINUTE = 'dcfbminute'
COLUMN_FAMILY_ID_SUM = 'dcfsum'
_COLUMN_ID = 'dc'
_ROW_KEY_DELIMETER = '#'
_table = None

def init():
    global _table
    # config.get_config()['bigtable']['project_id']
    _client = bigtable.Client(project=config.get_config()['bigtable']['project_id'], admin=True)
    _table_instance = bigtable.instance.Instance(config.get_config()['bigtable']['table_instance_id'], _client)
    _table = bigtable.table.Table(_TABLE_ID, _table_instance)
    # _table.exists() is not implemented so instead catch the exception
    try:
        _table.create()
    except:
        pass

    # reset the table content on each run for the demo
    for cf_name in [COLUMN_FAMILY_ID_LIST, COLUMN_FAMILY_ID_BY_MINUTE, COLUMN_FAMILY_ID_SUM]:
        cf = _table.column_family(cf_name)
        try:
            cf.delete()
        except:
            pass

        try:
            cf.create()
        except:
            pass

def _get_row_key(user_id, timestamp):
    return '{}{}{}'.format(user_id, _ROW_KEY_DELIMETER, timestamp)

def write_transaction(column_family_id, timestamp, user_id, spend):
    global _table
    if _table is None:
        init()

    row_key = '{}'.format(_get_row_key(user_id, timestamp))
    row = _table.row(row_key)
    row.set_cell(
        column_family_id,
        _COLUMN_ID,
        str(spend).encode('utf-8'))
    row.commit()

def read_transactions(column_family_id, user_id, from_timestamp, to_timestamp):
    global _table
    if _table is None:
        init()

    _table.read_rows(
        start_key=_get_row_key(user_id, from_timestamp),
        end_key=_get_row_key(user_id, to_timestamp),
        filter=_table.row_filters.FamilyNameRegexFilter(column_family_id)
    )

def read_transaction_at(column_family_id, user_id, timestamp):
    global _table
    if _table is None:
        init()

    _table.read_row(
        _get_row_key(user_id, timestamp),
        filter=_table.row_filters.FamilyNameRegexFilter(column_family_id)
    )
