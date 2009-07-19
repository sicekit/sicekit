# vim: set et! ts=2:

import ConfigParser, os

class _configuration(object):
	def __init__(self):
		defaults = {
			'cookiejar': os.path.expanduser('~/.sicekit_cookiejar'),
			'wiki_username': '',
			'wiki_password': '',
			'wiki_domain': None,
			'wiki_apiurl': '',
			'datapath': None,
			}
		for k in defaults.keys():
			setattr(self, k, defaults[k])

def getConfiguration():
	global _config
	if not globals().has_key("_config"):
		cfgfiles = ['.sicekitrc', os.path.expanduser('~/.sicekitrc'), '/etc/sicekit/sicekitrc']
		_config = _configuration()
		configparser = ConfigParser.ConfigParser()
		if len(configparser.read(cfgfiles)) == 0:
			print "W: No configuration file (%s) could be read." % cfgfiles
		for k in _config.__dict__.keys():
			if configparser.has_option('sicekit', k):
				setattr(_config, k, configparser.get('sicekit', k))
	return _config


