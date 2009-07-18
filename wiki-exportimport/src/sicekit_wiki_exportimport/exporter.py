# vim:set et!:

from wikitools import api
from optparse import OptionParser
import os
import re

class Exporter(object):
	def __init__(self, configuration, wiki):
		self.configuration = configuration
		self.wiki = wiki
		self.wikiversion = re.search("\d\.(\d\d)", self.wiki.siteinfo['generator'])

	def _buildCMListQuery(self, categoryname):
		params = {'action':'query', 'list':'categorymembers', 'cmprop':'ids|title|timestamp'}
		if not int(self.wikiversion.group(1)) >= 13:
			params['cmcategory'] = categoryname
		else:
			params['cmtitle'] = 'Category:%s' % categoryname
		return params

	def generatePageList(self):
		params = self._buildCMListQuery('Origin-SICEKIT')
		request = api.APIRequest(self.wiki, params)
		return request.query()['query']['categorymembers']

	def _buildDirFilename(self, page):
		(directory, filename) = page[u'title'].replace(':','/').rsplit('/', 1)
		return (os.path.join(self.options.export_path, directory), filename+'.xml')

	def writeDumpFile(self, page, xmldump):
		(directory, filename) = self._buildDirFilename(page)
		if not os.path.exists(directory): os.makedirs(directory)

		f = file(os.path.join(directory, filename), 'w')
		f.write(xmldump)
		f.close()

	def exportPage(self, page):
		title = page[u'title']
		print " === Exporting page %s ===" % title

		params = {'action':'query', 'titles':title,'export':'1'}
		request = api.APIRequest(self.wiki, params)
		xmldump = request.query()['query']['export']['*']

		self.writeDumpFile(page, xmldump)

		self.pagecount = self.pagecount + 1
		self.bytecount = self.bytecount + len(xmldump)

	def export(self, pages):
		self.pagecount = 0
		self.bytecount = 0
		map(self.exportPage, pages)

	def run(self, argv):
		op = OptionParser()
		op.add_option("-p", "--export-path", dest="export_path",
			help="directory to write exported files to")
		(self.options, args) = op.parse_args(argv)
		if self.options.export_path is None:
			print "E: --export-path needs to be specified."
			return 1

		pages = self.generatePageList()
		self.export(pages)
		print "I: Exported %d bytes in %d pages." % (self.bytecount, self.pagecount)
		return 0
