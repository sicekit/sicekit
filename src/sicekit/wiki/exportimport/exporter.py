# vim:set et!:

import os
import shutil
import xml.etree.ElementTree
from sicekit.wiki.exportimport.wikiutil import WikiUtil, XMLNS, APIRequest

class Exporter(object):
	def __init__(self, configuration, wiki):
		self.configuration = configuration
		self.wikiutil = WikiUtil(wiki)
		self.wiki = self.wikiutil.wiki

	def buildPageList(self):
		return self.wikiutil.retrieveCategoryMemberList('Origin-SICEKIT')

	def buildPageFilesystemPath(self, page, extension='.xml'):
		tmp = page[u'title'].replace(':','/').rsplit('/', 1)
		if len(tmp) == 1: tmp = ['', tmp[0]]
		(directory, filename) = tmp
		return (os.path.join(self.configuration.datapath, directory), filename+extension)

	def writeDumpFile(self, page, xmlElement):
		(directory, filename) = self.buildPageFilesystemPath(page)
		if not os.path.exists(directory): os.makedirs(directory)
		return self.wikiutil.writeXmlToFile(os.path.join(directory, filename), xmlElement)

	def exportPage(self, page):
		title = page[u'title']
		print "I: Exporting page %s." % title
		xml = self.wikiutil.retrievePageExportXml(title)

		# remove stuff we don't need / don't want to leak
		revision = xml.find(XMLNS+u'page/'+XMLNS+u'revision')
		if revision.find(XMLNS+u'comment'):
			revision.remove(revision.find(XMLNS+u'comment'))
		contributor = revision.find(XMLNS+u'contributor')
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

	def buildImageList(self, pages):
		titles = '|'.join(map(lambda x:x[u'title'], pages))
		params = {'action':'query','prop':'images','titles':titles}
		request = APIRequest(self.wiki, params)

		pages = request.query()['query']['pages']
		images = []
		# filter page list so we only get images
		for pageid in pages.keys():
			page = pages[pageid]
			if page.has_key('images'):
				images.extend(map(lambda img: img[u'title'], page['images']))
		return images

	def exportImage(self, title):
		print "I: Exporting image %s." % title
		params = {'action':'query','prop':'imageinfo','iiprop':'timestamp|url|sha1|comment','titles':title}
		request = APIRequest(self.wiki, params)
		pages = request.query()['query']['pages']
		page = pages[pages.keys()[0]]
		if page.has_key('missing'):
			print "W: Image %s does not exist." % title
			return
		imageinfo = page['imageinfo'][0]
		url = imageinfo[u'url']
		sha1 = imageinfo[u'sha1']
		directory = self.buildPageFilesystemPath(page)[0]
		if not os.path.exists(directory): os.makedirs(directory)
		image_path = os.path.join(*self.buildPageFilesystemPath(page, extension=''))
		sha1_path = os.path.join(*self.buildPageFilesystemPath(page, extension='.sha1'))
		bytes = self.wikiutil.downloadFile(url, image_path)
		f = file(sha1_path, 'w')
		f.write(sha1.encode('ascii'))
		f.close()
		self.bytecount = self.bytecount + bytes + 40 #sha1 is 40byte
		self.pagecount = self.pagecount + 2

	def run(self):
		if os.path.exists(self.configuration.datapath):
			print "I: Wiping export directory %s." % self.configuration.datapath
			shutil.rmtree(self.configuration.datapath)
		print "I: Exporting pages to %s." % self.configuration.datapath
		pages = self.buildPageList()
		self.pagecount = 0
		self.bytecount = 0
		map(self.exportPage, pages)
		print "I: Exporting images."
		images = self.buildImageList(pages)
		map(self.exportImage, images)

		print "I: Exported %d bytes in %d objects." % (self.bytecount, self.pagecount)
		return 0
