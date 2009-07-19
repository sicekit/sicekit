# vim:set et!:

import os
import xml.etree.ElementTree
from sicekit_wiki_exportimport.wikiutil import WikiUtil, XMLNS

class Exporter(object):
	def __init__(self, configuration, wiki):
		self.configuration = configuration
		self.wikiutil = WikiUtil(wiki)

	def buildPageList(self):
		return self.wikiutil.retrieveCategoryMemberList('Origin-SICEKIT')

	def buildPageFilesystemPath(self, page):
		tmp = page[u'title'].replace(':','/').rsplit('/', 1)
		if len(tmp) == 1: tmp = ['', tmp[0]]
		(directory, filename) = tmp
		return (os.path.join(self.configuration.datapath, directory), filename+'.xml')

	def writeDumpFile(self, page, xmlElement):
		(directory, filename) = self.buildPageFilesystemPath(page)
		if not os.path.exists(directory): os.makedirs(directory)
		return self.wikiutil.writeXmlToFile(os.path.join(directory, filename), xmlElement)

	def exportPage(self, page):
		title = page[u'title']
		print "I: Exporting page %s." % title
		xml = self.wikiutil.retrievePageExportXml(title)

		# remove stuff we don't need / don't want to leak
		contributor = xml.find(XMLNS+u'page/'+XMLNS+u'revision/'+XMLNS+u'contributor')
		contributor.find(XMLNS+u'username').text = u'SICEKIT'
		contributor.find(XMLNS+u'id').text = u'0'
		siteinfo = xml.find(XMLNS+u'siteinfo')
		siteinfo.find(XMLNS+u'sitename').text = u'SICEKIT'
		siteinfo.find(XMLNS+u'base').text = u'chrome:///sicekit'
		siteinfo.find(XMLNS+u'generator').text = u'SICEKIT'
		siteinfo.remove(siteinfo.find(XMLNS+u'namespaces'))

		bytes = self.writeDumpFile(page, xml)

		self.pagecount = self.pagecount + 1
		self.bytecount = self.bytecount + bytes

	def run(self):
		print "I: Exporting pages to %s." % self.configuration.datapath
		pages = self.buildPageList()
		self.pagecount = 0
		self.bytecount = 0
		map(self.exportPage, pages)
		print "I: Exported %d bytes in %d pages." % (self.bytecount, self.pagecount)
		return 0
