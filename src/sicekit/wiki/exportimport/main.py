# vim: set et!:
import sys
import os

from optparse import OptionParser
from sicekit.configuration import getConfiguration
from sicekit.wiki.wiki import getWiki
from sicekit.wiki.exportimport.exporter import Exporter
from sicekit.wiki.exportimport.importer import Importer

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
		configuration.datapath = os.path.abspath(configuration.datapath)

		wiki = getWiki(configuration)
		return mainmodule(configuration, wiki).run()

