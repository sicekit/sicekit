# vim:set et!:

from wikitools import api
from optparse import OptionParser
import os
import re
import xml.etree.ElementTree
from StringIO import StringIO

class Exporter(object):
	def __init__(self, configuration, wiki):
		self.configuration = configuration
		self.wiki = wiki
		if len(self.wiki.siteinfo) == 0:
			self.wiki.siteinfo['generator'] = 'MediaWiki (ancient; emulated) 1.11.0'

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
		tmp = page[u'title'].replace(':','/').rsplit('/', 1)
		if len(tmp) == 1: tmp = ['', tmp[0]]
		(directory, filename) = tmp
		return (os.path.join(self.options.export_path, directory), filename+'.xml')

	def writeDumpFile(self, page, xmldump):
		(directory, filename) = self._buildDirFilename(page)
		if not os.path.exists(directory): os.makedirs(directory)

		# add proper xml header
		if not "<?xml" in xmldump:
			xmldump = '<?xml version="1.0" encoding="utf-8"?>' + "\n" + xmldump

		f = file(os.path.join(directory, filename), 'w')
		f.write(xmldump)
		f.close()

	def exportPage(self, page):
		title = page[u'title']
		print "I: Exporting page %s." % title

		params = {'action':'query', 'titles':title,'export':'1'}
		request = api.APIRequest(self.wiki, params)
		xmldump = request.query()['query']['export']['*'].encode('utf-8') # convert to bytes
		doc = xml.etree.ElementTree.parse(StringIO(xmldump))
		contributor = doc.find(u'{http://www.mediawiki.org/xml/export-0.3/}page/{http://www.mediawiki.org/xml/export-0.3/}revision/{http://www.mediawiki.org/xml/export-0.3/}contributor')
		contributor.find(u'{http://www.mediawiki.org/xml/export-0.3/}username').text = u'SICEKIT'
		contributor.find(u'{http://www.mediawiki.org/xml/export-0.3/}id').text = u'0'
		siteinfo = doc.find(u'{http://www.mediawiki.org/xml/export-0.3/}siteinfo')
		siteinfo.find(u'{http://www.mediawiki.org/xml/export-0.3/}sitename').text = u'SICEKIT'
		siteinfo.find(u'{http://www.mediawiki.org/xml/export-0.3/}base').text = u'chrome:///sicekit'
		siteinfo.find(u'{http://www.mediawiki.org/xml/export-0.3/}generator').text = u'SICEKIT'
                siteinfo.remove(siteinfo.find(u'{http://www.mediawiki.org/xml/export-0.3/}namespaces'))

		self.writeDumpFile(page, xml.etree.ElementTree.tostring(doc.getroot(), 'utf-8'))

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
