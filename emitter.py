import config
import pubsub, queue, numpy as np, yaml

_USERS = {}

def init():
    # users
    users = config.get_config()['users']
    for user in users:
        for user in users:
            _USERS[user['user_id']] = user['user_info']

    # pubsub
    pubsub.create_subscription(config.get_config()['pubsub']['topic_id'], config.get_config()['pubsub']['subscription_id'])

def _emit_spend(timestamp, user_id, spend):
    pubsub.publish(config.get_config()['pubsub']['topic_id'], timestamp=timestamp, user_id=user_id, spend=spend)

def emit_spends(from_timestamp, to_timestamp):
    # the heap keeps the (<next event timestamp>, (user_id, spend))
    pq = queue.PriorityQueue()
    for u_id, u_info in _USERS.items():
        # decide the next expenditure for each user
        wait = int(np.random.exponential(u_info['scale']))
        pq.put((from_timestamp + wait, (u_id, 100)))

    while pq.qsize() > 0:
        next_spent = pq.get()
        when = next_spent[0]
        if when > to_timestamp: break
        u_id, spend = next_spent[1][0], next_spent[1][1]
        _emit_spend(when, u_id, spend)
        # decide the next expenditure after emit a signal
        wait = int(np.random.exponential(_USERS[u_id]['scale']))
        pq.put((when + wait, (u_id, 100)))


