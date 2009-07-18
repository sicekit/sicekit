from wikitools import api
from optparse import OptionParser
import os

class Exporter(object):
	def __init__(self, configuration, wiki):
		self.configuration = configuration
		self.wiki = wiki

	def generatePageList(self):

		# define the params for the query
		params = {'action':'query', 'list':'categorymembers', 'cmcategory':'Origin-SICEKIT', 'cmprop':'ids|title|timestamp'}
		# create the request object
		request = api.APIRequest(self.wiki, params)
		# query the API
		return request.query()['query']['categorymembers']

	def _buildDirFilename(self, page):
		(directory, filename) = page[u'title'].replace(':','/').rsplit('/', 1)
		return (os.path.join(self.options.export_path, directory), filename+'.xml')

	def exportPage(self, page):
		title = page[u'title']
		print " === Exporting page %s ===" % title

		params = {'action':'query', 'titles':title,'export':'1'}
		# create the request object
		request = api.APIRequest(self.wiki, params)
		# query the API
		xmldump = request.query()['query']['export']['*']

		(directory, filename) = self._buildDirFilename(page)
		if not os.path.exists(directory): os.makedirs(directory)

		f = file(os.path.join(directory, filename), 'w')
		f.write(xmldump)
		f.close()
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
