# vim:set et!:

from wikitools import api
from optparse import OptionParser
import os
import re
import xml.etree.ElementTree
from StringIO import StringIO
from datetime import datetime

class Importer(object):
	def __init__(self, configuration, wiki):
		self.configuration = configuration
		self.wiki = wiki
		self.wikiversion = re.search("\d\.(\d\d)", self.wiki.siteinfo['generator'])

	def _buildPageListPerDir(self, pagelist, dirname, fnames):
		for fname in fnames:
			path = os.path.join(dirname, fname)
			if os.path.isfile(path):
				print "I: Considering file %s." % path
				pagelist.append(self._readDumpFile(path))

	def _buildPageList(self):
		pagelist = []
		os.path.walk(self.options.import_path, self._buildPageListPerDir, pagelist)
		return pagelist

	def _readDumpFile(self, path):
		doc = xml.etree.ElementTree.ElementTree()
		doc.parse(path)
		title = doc.find('{http://www.mediawiki.org/xml/export-0.3/}page/{http://www.mediawiki.org/xml/export-0.3/}title').text
		revision = doc.find('{http://www.mediawiki.org/xml/export-0.3/}page/{http://www.mediawiki.org/xml/export-0.3/}revision')
		now = datetime.utcnow()
		# drop microsecond so there is no microsecond in isoformat()
		now = datetime(now.year, now.month, now.day, now.hour, now.minute, now.second, 0)
		revision.find('{http://www.mediawiki.org/xml/export-0.3/}timestamp').text = now.isoformat() + 'Z'
		revision.find('{http://www.mediawiki.org/xml/export-0.3/}id').text = '1'
		print 'I: Adding page "%s"' % title

		io = StringIO(xml.etree.ElementTree.tostring(doc.getroot()))
		io.name = "import.xml"

		return {u'title': title, u'io':io, u'xmldoc': doc}

	def _fetchPageText(self, title):
		params = {'action':'query', 'titles':title,'export':'1'}
		request = api.APIRequest(self.wiki, params)
		result = request.query()['query']
		if '-1' in result['pages'].keys(): return "" # page does not exist yet
		xmldump = result['export']['*'].encode('utf-8')
		doc = xml.etree.ElementTree.XML(xmldump)
		return doc.find('{http://www.mediawiki.org/xml/export-0.3/}page/{http://www.mediawiki.org/xml/export-0.3/}revision/{http://www.mediawiki.org/xml/export-0.3/}text').text

	def importPage(self, page):
		title = page[u'title']
		print "I: Importing page %s." % title

		oldtext = self._fetchPageText(title)
		newtext = page[u'xmldoc'].find('{http://www.mediawiki.org/xml/export-0.3/}page/{http://www.mediawiki.org/xml/export-0.3/}revision/{http://www.mediawiki.org/xml/export-0.3/}text').text
		if oldtext == newtext:
			print "I: Skipping, no changes."
			return

		# fetch import token
		params = {'action':'query', 'prop':'info', 'intoken':'import', 'titles':title}
		request = api.APIRequest(self.wiki, params)
		result = request.query()['query']
		if u'warnings' in result.keys():
			print 'W: Wiki gave warning: ' + result[u'warnings'][u'info'][u'*']
		pages = result['pages']
		importtoken = pages[pages.keys()[0]]['importtoken']

		# now post the page
		params = {'action':'import', 'token':importtoken}

		request = api.APIRequest(self.wiki, params)
		request.setMultipart()
		request.changeParam('xml', page[u'io'])
		result = request.query()

		if result[u'import'][0][u'revisions'] != 1:
			print "E: Page import failed. Wiki said:", result
			return 1

		self.pagecount = self.pagecount + 1
		self.changecount = self.changecount + result[u'import'][0][u'revisions']

	def _import(self, pages):
		print "I: Now importing pages."
		self.pagecount = 0
		self.changecount = 0
		map(self.importPage, pages)

	def run(self, argv):
		op = OptionParser()
		op.add_option("-p", "--import-path", dest="import_path",
				help="directory where import files are stored")
		(self.options, args) = op.parse_args(argv)
		if self.options.import_path is None:
			print "E: --import-path needs to be specified."
			return 1

		print "I: Looking for pages to import in %s." % self.options.import_path
		pagelist = self._buildPageList()
		self._import(pagelist)
		print "I: Imported %d pages, resulting in %d changes." % (self.pagecount, self.changecount)
		return 0
