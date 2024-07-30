import uuid
import pandas as pd
from deltalake import DeltaTable
from deltalake._internal import TableNotFoundError
import pyarrow as pa
import datetime

schema = pa.schema([
    pa.field('partition_year', pa.string(), nullable=False),
    pa.field('partition_month', pa.string(), nullable=False),
    pa.field('partition_day', pa.string(), nullable=False),
    pa.field('id', pa.int64(), nullable=False),
    pa.field('timestamp', pa.string(), nullable=False),
])

partition_column_names = ['partition_year', 'partition_month', 'partition_day']

now = datetime.datetime.now()
today_year = now.strftime('%Y')
today_month = now.strftime('%m')
today_day = now.strftime('%d')
base_ts = datetime.datetime.strptime(f"{today_year}-01-01", '%Y-%m-%d')

def find_delta_table(table_name: str) -> DeltaTable:
    storage_options = {
        "AWS_ALLOW_HTTP": "true",
        "AWS_ENDPOINT_URL": "http://localhost:4566",
        "AWS_S3_LOCKING_PROVIDER": "dynamodb",
        "AWS_REGION": "eu-west-1",
        "DELTA_DYNAMO_TABLE_NAME": "delta-table-lock-provider",
        "AWS_ACCESS_KEY_ID": 'mock_access_key',
        "AWS_SECRET_ACCESS_KEY": 'mock_secret_key',
    }
    table_uri = f"s3a://test-bucket/{table_name}"

    try:
        return DeltaTable(
            table_uri=table_uri,
            storage_options=storage_options
        )
    except TableNotFoundError:
        return DeltaTable.create(
            table_uri=table_uri,
            storage_options=storage_options,
            schema=schema,
            partition_by=partition_column_names,
        )


def upsert(table_name: str, data_frame: pd.DataFrame, use_equals: bool = False):
    dt = find_delta_table(table_name)

    predicate_components = [
        f"source.id = target.id",
        f"source.partition_year=target.partition_year",
        f"source.partition_month=target.partition_month",
        f"source.partition_day=target.partition_day",
        f"target.partition_year = '{today_year}'",
        f"target.partition_month = '{today_month}'"
    ]

    if use_equals:
        predicate_components.append(f"target.partition_day = '{today_day}'")
    else:
        predicate_components.append(f"target.partition_day IN ('{today_day}')")

    predicate = " AND ".join(predicate_components)
    print("Predicate:", predicate)

    table_merger = dt.merge(
        source=data_frame,
        source_alias="source",
        target_alias="target",
        predicate=predicate
    )

    table_merger.when_matched_update_all()
    table_merger.when_not_matched_insert_all()
    table_merger.execute()

# Generate seed and test data
seed_data = []
for i in range(0, 365):
    ts = base_ts + datetime.timedelta(days=i)
    seed_data.append({
        'partition_year': ts.strftime('%Y'),
        'partition_month': ts.strftime('%m'),
        'partition_day': ts.strftime('%d'),
        'id': i,
        'timestamp': ts
    })

first_update = [
    {
        'partition_year': now.strftime('%Y'),
        'partition_month': now.strftime('%m'),
        'partition_day': now.strftime('%d'),
        'id': 1234,
        'timestamp': now
    },
]

seed_data_frame = pd.DataFrame.from_records(seed_data)
first_update_frame = pd.DataFrame.from_records(first_update)

# Perform test
table_name = f"test-table-{uuid.uuid4()}"

upsert(table_name, seed_data_frame)

# This produces an extra partition in the scan the first time around, for reasons I don't understand
# We scan the expected partition, and one extra. The second time around, we only scan the exact expected partition
# upsert(table_name, first_update_frame, use_equals=True)

# This ignores the `IN` clause, and scans the entire month
# upsert(table_name, first_update_frame, use_equals=False)
