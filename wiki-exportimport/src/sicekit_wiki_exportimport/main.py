from wikitools import wiki

from sicekit_wiki_exportimport.configuration import getWikiConfiguration
from sicekit_wiki_exportimport.exporter import Exporter

class ExportImportMain(object):

	def __init__(self):
		pass

	def usage(self):
		print "Usage: exportimport export|import --help"
		return 1

	def run(self, argv):
		if len(argv) < 2:
			return self.usage()
		if argv[1] == 'export':
			mainmodule = Exporter
		elif argv[1] == 'import':
			mainmodule = Importer
		else:
			return self.usage()

		configuration = getWikiConfiguration()

		# create a Wiki object
		_wiki = wiki.Wiki(configuration.url)
		_wiki.cookiepath = configuration.cookie_filename
		_wiki.login(configuration.username, configuration.password, domain=configuration.domain, remember=True)

		_argv = []
		_argv.append(argv[0]+'_'+argv[1])
		_argv.extend(argv[2:])
		return mainmodule(configuration, _wiki).run(_argv)


