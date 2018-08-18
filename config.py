import json

_CONFIG_FILE = 'config.json'
_config = None

def _init():
	global _config
	_config = json.load(open(_CONFIG_FILE, 'r'))

def get_config():
	if _config is None:
		_init()
	return _config
