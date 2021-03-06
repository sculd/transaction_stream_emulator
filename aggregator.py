import config, pubsub, database
import os, json, csv
import pyspark
from pyspark.context import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import to_date
from pyspark.sql.functions  import date_format
from pyspark.sql.types import DateType
from pyspark.sql.functions import lit

# the pubsub subscription message queue is stored in the memory and
# when processing request comes in, it is consumed and written to
# a temp file.
# in the demo no synch mechanism is used, assuming only one
# request is process at any time.
_TEMP_FILE_NAME = 'aggregator_dummy.csv'

def write_rows_to_database(column_family_id, rows):
    for row in rows:
        print(row)
        database.write_transaction(column_family_id, row['timestamp'], row['user_id'], row['spend'])

def _consume_subscription_queue(subscription_id):
    with open(_TEMP_FILE_NAME, 'w') as outf:
        csv_writer = csv.writer(outf, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)

        process.header_written = False
        def on_msg(msg):
            print('msg: {}'.format(msg.decode()))
            js = json.loads(msg.decode())
            if not process.header_written:
                csv_writer.writerow(js.keys())
                process.header_written = True
            csv_writer.writerow(js.values())

        pubsub.listen_to_subscription(subscription_id, on_msg)

def _aggregate(from_timestamp, to_timestamp):
    spark = SparkSession.builder \
        .master("local") \
        .appName("Data cleaning") \
        .getOrCreate()

    df = spark.read \
        .format("csv") \
        .option("delimiter", ",") \
        .option("header", "true") \
        .option("mode", "DROPMALFORMED") \
        .load(_TEMP_FILE_NAME)

    # TODO: try to load with filters
    df = df.filter((df.timestamp > from_timestamp) & (df.timestamp < to_timestamp))

    # aggregate by hour to show the timeline of the spending per hour.
    df_truncate_by_hour = df.withColumn('timestamp', (df.timestamp / 3600).cast('int') * 3600)
    sum_by_hour_by_user_id = df_truncate_by_hour \
        .groupby(df_truncate_by_hour.user_id, df_truncate_by_hour.timestamp)\
        .agg({"spend": "sum"})\
        .withColumnRenamed('sum(spend)', 'spend')\
        .collect()

    # for the sum over the time range, add the timestamp @ the end boundary of the time range.
    # the sum is aggregated over the per-minute calculation, thus to avoid doing the minute level
    # aggregation again, would boost the speed when the volume is high.
    sum_by_user_id =  df_truncate_by_hour.groupby(df_truncate_by_hour.user_id)\
        .agg({"spend": "sum"})\
        .withColumnRenamed('sum(spend)', 'spend') \
        .withColumn("timestamp", lit(to_timestamp))\
        .collect()

    write_rows_to_database(database.COLUMN_FAMILY_ID_LIST, df.collect())
    write_rows_to_database(database.COLUMN_FAMILY_ID_BY_HOUR, sum_by_hour_by_user_id)
    write_rows_to_database(database.COLUMN_FAMILY_ID_SUM, sum_by_user_id)

def process(from_timestamp, to_timestamp):
    _consume_subscription_queue(config.get_config()['pubsub']['subscription_id'])
    _aggregate(from_timestamp, to_timestamp)


if __name__ == '__main__':
    import time
    to_timestamp = int(time.time())
    from_timestamp = to_timestamp - 6 * 3600
    _aggregate(from_timestamp, to_timestamp)
