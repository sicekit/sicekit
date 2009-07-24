# vim:set et!:

import os
import xml.etree.ElementTree
from StringIO import StringIO
from sicekit.wiki.exportimport.wikiutil import WikiUtil, XMLNS, APIRequest

class Importer(object):
	def __init__(self, configuration, wiki):
		self.configuration = configuration
		self.wikiutil = WikiUtil(wiki)
		self.wiki = self.wikiutil.wiki # WikiUtil modifies wiki

	def _buildPageListPerDir(self, pagelist, dirname, fnames):
		for fname in fnames:
			path = os.path.join(dirname, fname)
			if os.path.isfile(path) and path.endswith('.xml'):
				print "I: Considering file %s." % path
				pagelist.append(self.readDumpFile(path))

	def _buildPageList(self):
		pagelist = []
		os.path.walk(self.configuration.datapath, self._buildPageListPerDir, pagelist)
		return pagelist

	def readDumpFile(self, path):
		xmlEl = self.wikiutil.readXmlFromFile(path)
		title = xmlEl.find(XMLNS+u'page/'+XMLNS+u'title').text
		revision = xmlEl.find(XMLNS+u'page/'+XMLNS+u'revision')
		revision.find(XMLNS+u'timestamp').text = self.wikiutil.buildWikiTimestampNow()
		revision.find(XMLNS+u'id').text = '1'

		io = StringIO(xml.etree.ElementTree.tostring(xmlEl))
		io.name = "import.xml"

		return {u'title': title, u'io':io, u'xmldoc': xmlEl}

	def importPage(self, page):
		title = page[u'title']
		print "I: Importing page %s." % title

		oldpage = self.wikiutil.retrievePageExportXml(title)
		if oldpage is not None:
			oldtext = self.wikiutil.getPageTextFromXml(oldpage)
			newtext = self.wikiutil.getPageTextFromXml(page[u'xmldoc'])
			if oldtext == newtext:
				print "I: Skipping, no changes."
				return

		# fetch import token
		params = {'action':'query', 'prop':'info', 'intoken':'import', 'titles':title}
		request = APIRequest(self.wiki, params)
		result = request.query()['query']
		if u'warnings' in result.keys():
			print 'W: Wiki gave warning: ' + result[u'warnings'][u'info'][u'*']
		pages = result['pages']
		importtoken = pages[pages.keys()[0]]['importtoken']

		# now post the page
		params = {'action':'import', 'token':importtoken}
		request = APIRequest(self.wiki, params)
		request.setMultipart()
		request.changeParam('xml', page[u'io'])
		result = request.query()

		if result[u'import'][0][u'revisions'] != 1:
			print "E: Page import failed. Wiki said:", result
			return 1

		self.pagecount = self.pagecount + 1
		self.changecount = self.changecount + result[u'import'][0][u'revisions']

	def run(self):
		print "I: Looking for pages to import in %s." % self.configuration.datapath
		pagelist = self._buildPageList()
		print "I: Now importing pages."
		self.pagecount = 0
		self.changecount = 0
		map(self.importPage, pagelist)

		print "I: Imported %d pages, resulting in %d changes." % (self.pagecount, self.changecount)
		return 0
