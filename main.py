import emitter, pubsub, aggregator, database
import time

def init():
    emitter.init()
    database.init_and_reset()

if __name__ == '__main__':
    init()
    to_timestamp = int(time.time())
    from_timestamp = to_timestamp - 10 * 3600
    emitter.emit_spends(from_timestamp, to_timestamp)
    aggregator.process(from_timestamp, to_timestamp)
