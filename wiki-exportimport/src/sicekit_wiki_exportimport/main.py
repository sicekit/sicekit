# vim: set et!:
import sys

from wikitools import wiki
from optparse import OptionParser
from sicekit_wiki_exportimport.configuration import getConfiguration
from sicekit_wiki_exportimport.exporter import Exporter
from sicekit_wiki_exportimport.importer import Importer

class ExportImportMain(object):

	def __init__(self):
		pass

	def parseopts(self):
		op = OptionParser()
		op.add_option("-d", "--datapath", dest="datapath",
				help="directory where import files are stored",
				metavar="DIRECTORY")
		op.add_option("--export", action="store_true", dest="mode_export",
				help="export pages from wiki into files")
		op.add_option("--import", action="store_true", dest="mode_import",
				help="import pages from files into the wiki")
		return op.parse_args(self.argv)

	def run(self, argv):
		self.argv = argv
		configuration = getConfiguration()

		(cmdlineopts, cmdlineargs) = self.parseopts()
		if cmdlineopts.mode_export and not cmdlineopts.mode_import:
			mainmodule = Exporter
		elif cmdlineopts.mode_import and not cmdlineopts.mode_export:
			mainmodule = Importer
		else:
			print "E: Either --export or --import needs to be specified."
			return 1

		if not cmdlineopts.datapath is None:
			configuration.datapath = cmdlineopts.datapath
		if configuration.datapath is None:
			print "E: --data-path needs to be specified."
			return 1

		# create the Wiki object
		_wiki = wiki.Wiki(configuration.wiki_apiurl)
		_wiki.cookiepath = configuration.cookiejar
		if not _wiki.login(configuration.wiki_username, configuration.wiki_password, domain=configuration.wiki_domain, remember=True):
			print "E: Login failed early."
			return 1
		if not _wiki.isLoggedIn():
			print "E: Login failed."
			return 1

		return mainmodule(configuration, _wiki).run()


