# vim:set et!:

from wikitools.api import APIRequest
import re
import xml.etree.ElementTree
from datetime import datetime
import urllib2

XMLNS = u'{http://www.mediawiki.org/xml/export-0.3/}'

class WikiUtil(object):
	def __init__(self, wiki):
		self.wiki = wiki
		if len(self.wiki.siteinfo) == 0:
			self.wiki.siteinfo['generator'] = 'MediaWiki (ancient; emulated) 1.11.0'

		self.wiki.wikiversion = re.search("\d\.(\d\d)", self.wiki.siteinfo['generator'])

	def _buildCategoryMemberListQuery(self, categoryname):
		params = {'action':'query', 'list':'categorymembers', 'cmprop':'ids|title|timestamp'}
		if not int(self.wiki.wikiversion.group(1)) >= 13:
			params['cmcategory'] = categoryname
		else:
			params['cmtitle'] = 'Category:%s' % categoryname
		return params

	def retrieveCategoryMemberList(self, categoryname):
		params = self._buildCategoryMemberListQuery(categoryname)
		request = APIRequest(self.wiki, params)
		return request.query()['query']['categorymembers']

	def writeXmlToFile(self, path, xmlElement):
		xmlbytes = xml.etree.ElementTree.tostring(xmlElement, 'utf-8')
		# add proper xml header with encoding
		if not "<?xml" in xmlbytes:
			xmlbytes = '<?xml version="1.0" encoding="utf-8"?>' + "\n" + xmlbytes
		f = file(path, 'w')
		f.write(xmlbytes)
		f.close()
		return len(xmlbytes)

	def readXmlFromFile(self, path):
		doc = xml.etree.ElementTree.ElementTree()
		doc.parse(path)
		return doc.getroot()

	def buildWikiTimestampNow(self):
		now = datetime.utcnow()
		# drop microsecond so there is no microsecond in isoformat()
		now = datetime(now.year, now.month, now.day, now.hour, now.minute, now.second, 0)
		return now.isoformat() + 'Z'

	def getPageTextFromXml(self, xmlElement):
		text = xmlElement.find(XMLNS+u'page/'+XMLNS+u'revision/'+XMLNS+u'text').text
		return text

	def retrievePageExportXml(self, title):
		params = {'action':'query', 'titles':title,'export':'1'}
		request = APIRequest(self.wiki, params)
		result = request.query()['query']
		if '-1' in result['pages'].keys(): return None # page does not exist yet
		xmlbytes = result['export']['*'].encode('utf-8') # convert to bytes
		return xml.etree.ElementTree.XML(xmlbytes)

	def downloadFile(self, url, path):
		request = urllib2.Request(url)
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.wiki.cookies))
		data = opener.open(request)
		f = file(path, 'w')
		buffer = data.read()
		f.write(buffer)
		f.close()
		return len(buffer)

