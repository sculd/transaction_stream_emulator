import pubsub, queue, numpy as np, yaml, time

_PUBUB_TOPIC_ID = 'demo_topic_id'
_PUBUB_SUBSCRIPTION_ID = 'demo_subscription_id'
_USERS = {}

def initialize(user_config_yaml_file_name = 'users.yaml'):
	# users
	with open(user_config_yaml_file_name, 'r') as fs:
	    try:
	        user_config = yaml.load(fs)

	    except yaml.YAMLError as ex:
	        print(ex)

	# pubsub
	pubsub.create_subscription(_PUBUB_TOPIC_ID, _PUBUB_SUBSCRIPTION_ID)

def _emit_spend(timestamp, user_id, spend):
	pubsub.publish(_PUBUB_TOPIC_ID, timestamp, user_id, spend)

def emit_spends(from_timestamp, to_timestamp):
	t = 1
	# the heap keeps the (<next event timestamp>, (user_id, spend))
	pq = queue.PriorityQueue()
	for u in _USERS:
		# decide the next expenditure for each user
		pq.put(np.random.exponential(u['scale']))

	while pq.qsize() > 0:
		next_spent = pq.get()
		if next_spent[0] > to_timestamp: break
		# decide the next expenditure after emit a signal
		_emit_spend(next_spent[0], *next_spent[1])

if __name__ == '__main__':
	initialize()
	to_timestamp = time.time()
	from_timestamp = to_timestamp - 6 * 3600
	emit_spends(from_timestamp, to_timestamp)
