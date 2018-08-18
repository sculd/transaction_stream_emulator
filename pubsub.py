from collections import defaultdict
from queue import deque
import json

# dict of topic to set of subscriptions
_SUBSCRIPTIONS = defaultdict(set)

# keeps messages published to subscription.
# note: pubsub does not maintain anything if a topic has no subscriber.
# the messages are piled in the received order.
_PUBLISHED_MESSAGES = defaultdict(deque)

def publish(topic_id, **data):
    def _get_payload():
        return json.dumps(data).encode()
    print('data: {}'.format(json.dumps(data)))
    for sub_id in _SUBSCRIPTIONS[topic_id]:
        _PUBLISHED_MESSAGES[sub_id].append(_get_payload())

def create_subscription(topic_id, subscription_id):
    if subscription_id not in _SUBSCRIPTIONS[topic_id]:
        _SUBSCRIPTIONS[topic_id].add(subscription_id)

def delete_subscription(topic_id, subscription_id):
    _SUBSCRIPTIONS[topic_id].discard(subscription_id)

def listen_to_subscription(subscription_id, callback):
    while len(_PUBLISHED_MESSAGES[subscription_id]) > 0:
        msg = _PUBLISHED_MESSAGES[subscription_id].popleft()
        callback(msg)
