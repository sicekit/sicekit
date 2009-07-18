#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This module offers a wide variety of page generators. A page generator is an
object that is iterable (see http://www.python.org/dev/peps/pep-0255/ ) and
that yields page objects on which other scripts can then work.

In general, there is no need to run this script directly. It can, however,
be run for testing purposes. It will then print the page titles to standard
output.

These parameters are supported to specify which pages titles to print:

&params;
"""
__version__='$Id: pagegenerators.py 6942 2009-06-07 05:24:19Z purodha $'

parameterHelp = """\
-cat              Work on all pages which are in a specific category.
                  Argument can also be given as "-cat:categoryname" or
                  as "-cat:categoryname|fromtitle".

-catr             Like -cat, but also recursively includes pages in
                  subcategories, sub-subcategories etc. of the
                  given category.
                  Argument can also be given as "-catr:categoryname" or
                  as "-catr:categoryname|fromtitle".

-subcats          Work on all subcategories of a specific category.
                  Argument can also be given as "-subcats:categoryname" or
                  as "-subcats:categoryname|fromtitle".

-subcatsr         Like -subcats, but also includes sub-subcategories etc. of
                  the given category.
                  Argument can also be given as "-subcatsr:categoryname" or
                  as "-subcatsr:categoryname|fromtitle".

-uncat            Work on all pages which are not categorised.

-uncatcat         Work on all categories which are not categorised.

-uncatfiles       Work on all files which are not categorised.

-file             Read a list of pages to treat from the named text file.
                  Page titles in the file must be enclosed with [[brackets]]
                  or separated by newlines. Argument can also be given as
                  "-file:filename".

-filelinks        Work on all pages that use a certain image/media file.
                  Argument can also be given as "-filelinks:filename".

-yahoo            Work on all pages that are found in a Yahoo search.
                  Depends on python module pYsearch.  See yahoo_appid in
                  config.py for instructions.

-search           Work on all pages that are found in a MediaWiki search
                  across all namespaces.

-google           Work on all pages that are found in a Google search.
                  You need a Google Web API license key. Note that Google
                  doesn't give out license keys anymore. See google_key in
                  config.py for instructions.
                  Argument can also be given as "-google:searchstring".

-namespace        Filters the page generator to only yield pages in the
                  specified namespaces.  Separate multiple namespace
                  numbers with commas.

-interwiki        Work on the given page and all equivalent pages in other
                  languages. This can, for example, be used to fight
                  multi-site spamming.
                  Attention: this will cause the bot to modify
                  pages on several wiki sites, this is not well tested,
                  so check your edits!

-links            Work on all pages that are linked from a certain page.
                  Argument can also be given as "-links:linkingpagetitle".

-new              Work on the 60 newest pages. If given as -new:x, will work
                  on the x newest pages.

-imagelinks       Work on all images that are linked from a certain page.
                  Argument can also be given as "-imagelinks:linkingpagetitle".

-newimages        Work on the 100 newest images. If given as -newimages:x,
                  will work on the x newest images.

-ref              Work on all pages that link to a certain page.
                  Argument can also be given as "-ref:referredpagetitle".

-start            Specifies that the robot should go alphabetically through
                  all pages on the home wiki, starting at the named page.
                  Argument can also be given as "-start:pagetitle".

                  You can also include a namespace. For example,
                  "-start:Template:!" will make the bot work on all pages
                  in the template namespace.

-prefixindex      Work on pages commencing with a common prefix.

-titleregex       Work on titles that match the given regular expression.

-transcludes      Work on all pages that use a certain template.
                  Argument can also be given as "-transcludes:Template:Title".

-unusedfiles      Work on all description pages of images/media files that are
                  not used anywhere.
                  Argument can be given as "-unusedfiles:n" where
                  n is the maximum number of articles to work on.

-unwatched        Work on all articles that are not watched by anyone.
                  Argument can be given as "-unwatched:n" where
                  n is the maximum number of articles to work on.

-usercontribs     Work on all articles that were edited by a certain user :
                  Example : -usercontribs:DumZiBoT

-weblink          Work on all articles that contain an external link to
                  a given URL; may be given as "-weblink:url"

-withoutinterwiki Work on all pages that don't have interlanguage links.
                  Argument can be given as "-withoutinterwiki:n" where
                  n is some number (??).

-random           Work on random pages returned by [[Special:Random]].
                  Can also be given as "-random:n" where n is the number
                  of pages to be returned, else 10 pages are returned.

-randomredirect   Work on random redirect target pages returned by
                  [[Special:Randomredirect]].  Can also be given as
                  "-randomredirect:n" where n is the number of pages to be
                  returned, else 10 pages are returned.

-gorandom         Specifies that the robot should starting at the random pages 
                  returned by [[Special:Random]].

-recentchanges    Work on new and edited pages returned by [[Special:Recentchanges]].
                  Can also be given as "-recentchanges:n" where n is the number
                  of pages to be returned, else 100 pages are returned.
"""



docuReplacements = {
    '&params;': parameterHelp
}


# Standard library imports
import re, codecs, sys
import threading, Queue, traceback
import urllib, urllib2, time

# Application specific imports
import wikipedia, date, catlib
import config


class ThreadedGenerator(threading.Thread):
    """Look-ahead generator class.

    Runs a generator in a separate thread and queues the results; can
    be called like a regular generator.

    Subclasses should override self.generator, _not_ self.run

    Important: the generator thread will stop itself if the generator's
    internal queue is exhausted; but, if the calling program does not use
    all the generated values, it must call the generator's stop() method to
    stop the background thread.  Example usage:

    >>> gen = ThreadedGenerator(target=foo)
    >>> try:
    ...     for data in gen:
    ...         do_work(data)
    ... finally:
    ...     gen.stop()

    """

    def __init__(self, group=None, target=None, name="GeneratorThread",
                 args=(), kwargs=None, qsize=65536):
        """Constructor.  Takes same keyword arguments as threading.Thread.

        target must be a generator function (or other callable that returns
        an iterable object).

        @param qsize: The size of the lookahead queue. The larger the qsize,
        the more values will be computed in advance of use (which can eat
        up memory and processor time).
        @type qsize: int

        """
        if kwargs is None:
            kwargs = {}
        if target:
            self.generator = target
        if not hasattr(self, "generator"):
            raise RuntimeError("No generator for ThreadedGenerator to run.")
        self.args, self.kwargs = args, kwargs
        threading.Thread.__init__(self, group=group, name=name)
        self.queue = Queue.Queue(qsize)
        self.finished = threading.Event()

    def __iter__(self):
        """Iterate results from the queue."""
        if not self.isAlive() and not self.finished.isSet():
            self.start()
        # if there is an item in the queue, yield it, otherwise wait
        while not self.finished.isSet():
            try:
                yield self.queue.get(True, 0.25)
            except Queue.Empty:
                pass
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        """Stop the background thread."""
##        if not self.finished.isSet():
##            wikipedia.output("DEBUG: signalling %s to stop." % self)
        self.finished.set()

    def run(self):
        """Run the generator and store the results on the queue."""
        self.__gen = self.generator(*self.args, **self.kwargs)
        for result in self.__gen:
            while True:
                if self.finished.isSet():
##                    wikipedia.output("DEBUG: %s received stop signal." % self)
                    return
                try:
                    self.queue.put_nowait(result)
                except Queue.Full:
                    time.sleep(0.25)
                    continue
                break
        # wait for queue to be emptied, then kill the thread
        while not self.finished.isSet() and not self.queue.empty():
            time.sleep(0.25)
        self.stop()
##        wikipedia.output("DEBUG: %s stopped because generator exhausted." % self)


def AllpagesPageGenerator(start ='!', namespace = None, includeredirects = True, site = None):
    """
    Using the Allpages special page, retrieve all articles' titles, and yield
    page objects.
    If includeredirects is False, redirects are not included. If
    includeredirects equals the string 'only', only redirects are added.
    """
    if site is None:
        site = wikipedia.getSite()
    for page in site.allpages(start = start, namespace = namespace, includeredirects = includeredirects):
        yield page

def PrefixingPageGenerator(prefix, namespace = None, includeredirects = True, site = None):
    if site is None:
        site = wikipedia.getSite()
    page = wikipedia.Page(site, prefix)
    if namespace is None:
        namespace = page.namespace()
    title = page.titleWithoutNamespace()
    for page in site.prefixindex(prefix = title, namespace = namespace, includeredirects = includeredirects):
        yield page

def NewpagesPageGenerator(number = 100, get_redirect = False, repeat = False, site = None, namespace = 0):
    if site is None:
        site = wikipedia.getSite()
    for page in site.newpages(number=number, get_redirect=get_redirect, repeat=repeat, namespace=namespace):
        yield page[0]

def FileLinksGenerator(referredImagePage):
    for page in referredImagePage.usingPages():
        yield page

def ImagesPageGenerator(pageWithImages):
    for imagePage in pageWithImages.imagelinks(followRedirects = False, loose = True):
        yield imagePage

def UnusedFilesGenerator(number = 100, repeat = False, site = None, extension = None):
    if site is None:
        site = wikipedia.getSite()
    for page in site.unusedfiles(number=number, repeat=repeat, extension=extension):
        yield wikipedia.ImagePage(page.site(), page.title())

def WithoutInterwikiPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = wikipedia.getSite()
    for page in site.withoutinterwiki(number=number, repeat=repeat):
        yield page

def InterwikiPageGenerator(page):
    yield page
    for iwPage in page.interwiki():
        yield iwPage

def ReferringPageGenerator(referredPage, followRedirects=False,
                           withTemplateInclusion=True,
                           onlyTemplateInclusion=False):
    '''Yields all pages referring to a specific page.'''
    for page in referredPage.getReferences(followRedirects,
                                           withTemplateInclusion,
                                           onlyTemplateInclusion):
        yield page

def CategorizedPageGenerator(category, recurse=False, start=None):
    '''
    Yields all pages in a specific category.

    If recurse is True, pages in subcategories are included as well; if
    recurse is an int, only subcategories to that depth will be included
    (e.g., recurse=2 will get pages in subcats and sub-subcats, but will
    not go any further).
    If start is a string value, only pages whose title comes after start
    alphabetically are included.
    '''
    for page in category.articles(recurse = recurse, startFrom = start):
        if page.title() >= start:
            yield page

def SubCategoriesPageGenerator(category, recurse=False, start=None):
    '''
    Yields all subcategories in a specific category.

    If recurse is True, pages in subcategories are included as well; if
    recurse is an int, only subcategories to that depth will be included
    (e.g., recurse=2 will get pages in subcats and sub-subcats, but will
    not go any further).
    '''
    for page in category.subcategories(recurse = recurse, startFrom = start):
        yield page

def UnCategorizedCategoryGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = wikipedia.getSite()
    for page in site.uncategorizedcategories(number=number, repeat=repeat):
        yield page

def UnCategorizedImageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = wikipedia.getSite()
    for page in site.uncategorizedimages(number=number, repeat=repeat):
        yield page

def NewimagesPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = wikipedia.getSite()
    for page in site.newimages(number, repeat=repeat):
        yield page[0]

def UnCategorizedPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = wikipedia.getSite()
    for page in site.uncategorizedpages(number=number, repeat=repeat):
        yield page

def LonelyPagesPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = wikipedia.getSite()
    for page in site.lonelypages(number=number, repeat=repeat):
        yield page

def UnwatchedPagesPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = wikipedia.getSite()
    for page in site.unwatchedpages(number=number, repeat=repeat):
        yield page

def AncientPagesPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = wikipedia.getSite()
    for page in site.ancientpages(number=number, repeat=repeat):
        yield page[0]

def DeadendPagesPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = wikipedia.getSite()
    for page in site.deadendpages(number=number, repeat=repeat):
        yield page

def LongPagesPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = wikipedia.getSite()
    for page in site.longpages(number=number, repeat=repeat):
        yield page[0]

def ShortPagesPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = wikipedia.getSite()
    for page in site.shortpages(number=number, repeat=repeat):
        yield page[0]

def LinkedPageGenerator(linkingPage):
    """Yields all pages linked from a specific page."""
    for page in linkingPage.linkedPages():
        yield page

def RandomPageGenerator(number = 10, site = None):
    if site is None:
        site = wikipedia.getSite()
    for i in range(number):
        yield site.randompage()

def RandomRedirectPageGenerator(number = 10, site = None):
    if site is None:
        site = wikipedia.getSite()
    for i in range(number):
        yield site.randomredirectpage()
 
def RecentchangesPageGenerator(number = 100, site = None):
    if site is None:
        site = wikipedia.getSite()
    for page in site.recentchanges(number=number):
        yield page[0]

def TextfilePageGenerator(filename=None, site=None):
    '''
    Read a file of page links between double-square-brackets or, in
    alternative, separated by newlines, and return them as a list of Page
    objects. filename is the name of the file that should be read. If no
    name is given, the generator prompts the user.
    '''
    if filename is None:
        filename = wikipedia.input(u'Please enter the filename:')
    if site is None:
        site = wikipedia.getSite()
    f = codecs.open(filename, 'r', config.textfile_encoding)
    R = re.compile(ur'\[\[(.+?)(?:\]\]|\|)') # title ends either before | or before ]]
    pageTitle = None
    for pageTitle in R.findall(f.read()):
        # If the link doesn't refer to this site, the Page constructor
        # will automatically choose the correct site.
        # This makes it possible to work on different wikis using a single
        # text file, but also could be dangerous because you might
        # inadvertently change pages on another wiki!
        yield wikipedia.Page(site, pageTitle)
    if pageTitle is None:
        f.seek(0)
        for title in f:
            title = title.strip()
            if title:
                yield wikipedia.Page(site, title)
    f.close()

def PagesFromTitlesGenerator(iterable, site = None):
    """Generates pages from the titles (unicode strings) yielded by iterable"""
    if site is None:
        site = wikipedia.getSite()
    for title in iterable:
        if not isinstance(title, basestring):
            break
        yield wikipedia.Page(site, title)

def LinksearchPageGenerator(link, step=500, site=None):
    """Yields all pages that include a specified link, according to
    [[Special:Linksearch]].
    """
    if site is None:
        site = wikipedia.getSite()
    for page in site.linksearch(link, limit=step):
        yield page

def UserContributionsGenerator(username, number = 250, namespaces = [], site = None ):
    """
    Yields number unique pages edited by user:username
    namespaces : list of namespace numbers to fetch contribs from
    """
    import urllib
    if site is None:
        site = wikipedia.getSite()
    if number > 500:
        # the api does not allow more than 500 results for anonymous users
        number = 500
    apiQ = site.api_address() + 'action=query&list=usercontribs&ucuser='
    apiQ += urllib.quote(username.encode(site.encoding()))
    apiQ += '&ucprop=title&uclimit=%s&format=xml' % number
    if namespaces:
        apiQ += '&ucnamespace=%s' % '|'.join(map(str, namespaces))
    titlesRe = re.compile('title="(.*?)"')
    ucstartRe = re.compile('ucstart="(.*?)"')
    ucstart = ''
    # An user is likely to contribute on several pages,
    # keeping track of titles
    titleList = []
    while True:
        result = site.getUrl(apiQ + ucstart)
        for title in titlesRe.findall(result):
            if not title in titleList:
                titleList.append(title)
                yield wikipedia.Page(site, title)
        m = ucstartRe.search(result)
        if m:
            ucstart = '&ucstart=' + m.group(1)
        else:
            break

def SearchPageGenerator(query, number = 100, namespaces = None, site = None):
    """
    Provides a list of results using the internal MediaWiki search engine
    """
    if site is None:
        site = wikipedia.getSite()
    for page in site.search(query, number=number, namespaces = namespaces):
        yield page[0]

class YahooSearchPageGenerator:
    '''
    To use this generator, install pYsearch
    '''
    def __init__(self, query = None, count = 100, site = None): # values larger than 100 fail
        self.query = query or wikipedia.input(u'Please enter the search query:')
        self.count = count
        if site is None:
            site = wikipedia.getSite()
        self.site = site

    def queryYahoo(self, query):
       from yahoo.search.web import WebSearch
       srch = WebSearch(config.yahoo_appid, query=query, results=self.count)

       dom = srch.get_results()
       results = srch.parse_results(dom)
       for res in results:
           url = res.Url
           yield url

    def __iter__(self):
        # restrict query to local site
        localQuery = '%s site:%s' % (self.query, self.site.hostname())
        base = 'http://%s%s' % (self.site.hostname(), self.site.nice_get_address(''))
        for url in self.queryYahoo(localQuery):
            if url[:len(base)] == base:
                title = url[len(base):]
                page = wikipedia.Page(self.site, title)
                yield page

class GoogleSearchPageGenerator:
    '''
    To use this generator, you must install the pyGoogle module from
    http://pygoogle.sf.net/ and get a Google Web API license key from
    http://www.google.com/apis/index.html . The google_key must be set to your
    license key in your configuration.
    '''
    def __init__(self, query = None, site = None):
        self.query = query or wikipedia.input(u'Please enter the search query:')
        if site is None:
            site = wikipedia.getSite()
        self.site = site

    #########
    # partially commented out because it is probably not in compliance with Google's "Terms of
    # service" (see 5.3, http://www.google.com/accounts/TOS?loc=US)
    def queryGoogle(self, query):
        #if config.google_key:
        if True:
            #try:
                for url in self.queryViaSoapApi(query):
                    yield url
                return
            #except ImportError:
                #pass
        # No google license key, or pygoogle not installed. Do it the ugly way.
        #for url in self.queryViaWeb(query):
        #    yield url

    def queryViaSoapApi(self, query):
        import google
        google.LICENSE_KEY = config.google_key
        offset = 0
        estimatedTotalResultsCount = None
        while not estimatedTotalResultsCount or offset < estimatedTotalResultsCount:
            while (True):
                # Google often yields 502 errors.
                try:
                    wikipedia.output(u'Querying Google, offset %i' % offset)
                    data = google.doGoogleSearch(query, start = offset, filter = False)
                    break
                except KeyboardInterrupt:
                    raise
                except:
                    # SOAPpy.Errors.HTTPError or SOAP.HTTPError (502 Bad Gateway)
                    # can happen here, depending on the module used. It's not easy
                    # to catch this properly because pygoogle decides which one of
                    # the soap modules to use.
                    wikipedia.output(u"An error occured. Retrying in 10 seconds...")
                    time.sleep(10)
                    continue

            for result in data.results:
                #print 'DBG: ', result.URL
                yield result.URL
            # give an estimate of pages to work on, but only once.
            if not estimatedTotalResultsCount:
                wikipedia.output(u'Estimated total result count: %i pages.' % data.meta.estimatedTotalResultsCount)
            estimatedTotalResultsCount = data.meta.estimatedTotalResultsCount
            #print 'estimatedTotalResultsCount: ', estimatedTotalResultsCount
            offset += 10

    #########
    # commented out because it is probably not in compliance with Google's "Terms of
    # service" (see 5.3, http://www.google.com/accounts/TOS?loc=US)

    #def queryViaWeb(self, query):
        #"""
        #Google has stopped giving out API license keys, and sooner or later
        #they will probably shut down the service.
        #This is a quick and ugly solution: we just grab the search results from
        #the normal web interface.
        #"""
        #linkR = re.compile(r'<a href="([^>"]+?)" class=l>', re.IGNORECASE)
        #offset = 0

        #while True:
            #wikipedia.output("Google: Querying page %d" % (offset / 100 + 1))
            #address = "http://www.google.com/search?q=%s&num=100&hl=en&start=%d" % (urllib.quote_plus(query), offset)
            ## we fake being Firefox because Google blocks unknown browsers
            #request = urllib2.Request(address, None, {'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.8) Gecko/20051128 SUSE/1.5-0.1 Firefox/1.5'})
            #urlfile = urllib2.urlopen(request)
            #page = urlfile.read()
            #urlfile.close()
            #for url in linkR.findall(page):
                #yield url
            #if "<div id=nn>" in page: # Is there a "Next" link for next page of results?
                #offset += 100  # Yes, go to next page of results.
            #else:
                #return
    #########

    def __iter__(self):
        # restrict query to local site
        localQuery = '%s site:%s' % (self.query, self.site.hostname())
        base = 'http://%s%s' % (self.site.hostname(), self.site.nice_get_address(''))
        for url in self.queryGoogle(localQuery):
            if url[:len(base)] == base:
                title = url[len(base):]
                page = wikipedia.Page(self.site, title)
                # Google contains links in the format http://de.wikipedia.org/wiki/en:Foobar
                if page.site() == self.site:
                    yield page

def MySQLPageGenerator(query, site = None):
    import MySQLdb as mysqldb
    if site is None:
        site = wikipedia.getSite()
    conn = mysqldb.connect(config.db_hostname, db = site.dbName(),
                           user = config.db_username,
                           passwd = config.db_password)
    cursor = conn.cursor()
    wikipedia.output(u'Executing query:\n%s' % query)
    query = query.encode(site.encoding())
    cursor.execute(query)
    while True:
        try:
            namespaceNumber, pageName = cursor.fetchone()
            print namespaceNumber, pageName
        except TypeError:
            # Limit reached or no more results
            break
        #print pageName
        if pageName:
            namespace = site.namespace(namespaceNumber)
            pageName = unicode(pageName, site.encoding())
            if namespace:
                pageTitle = '%s:%s' % (namespace, pageName)
            else:
                pageTitle = pageName
            page = wikipedia.Page(site, pageTitle)
            yield page

def YearPageGenerator(start = 1, end = 2050, site = None):
    if site is None:
        site = wikipedia.getSite()
    wikipedia.output(u"Starting with year %i" % start)
    for i in xrange(start, end + 1):
        if i % 100 == 0:
            wikipedia.output(u'Preparing %i...' % i)
        # There is no year 0
        if i != 0:
            current_year = date.formatYear(site.lang, i )
            yield wikipedia.Page(site, current_year)

def DayPageGenerator(startMonth = 1, endMonth = 12, site = None):
    if site is None:
        site = wikipedia.getSite()
    fd = date.FormatDate(site)
    firstPage = wikipedia.Page(site, fd(startMonth, 1))
    wikipedia.output(u"Starting with %s" % firstPage.aslink())
    for month in xrange(startMonth, endMonth+1):
        for day in xrange(1, date.getNumberOfDaysInMonth(month)+1):
            yield wikipedia.Page(site, fd(month, day))

def NamespaceFilterPageGenerator(generator, namespaces, site = None):
    """
    Wraps around another generator. Yields only those pages that are in one
    of the given namespaces.

    The namespace list can contain both integers (namespace numbers) and
    strings/unicode strings (namespace names).
    """
    # convert namespace names to namespace numbers
    if site is None:
        site = wikipedia.getSite()
    for i in xrange(len(namespaces)):
        ns = namespaces[i]
        if isinstance(ns, unicode) or isinstance(ns, str):
            index = site.getNamespaceIndex(ns)
            if index is None:
                raise ValueError(u'Unknown namespace: %s' % ns)
            namespaces[i] = index
    for page in generator:
        if page.namespace() in namespaces:
            yield page

def RedirectFilterPageGenerator(generator):
    """
    Wraps around another generator. Yields only those pages that are not redirects.
    """
    for page in generator:
        if not page.isRedirectPage():
            yield page

def DuplicateFilterPageGenerator(generator):
    """
    Wraps around another generator. Yields all pages, but prevents
    duplicates.
    """
    seenPages = dict()
    for page in generator:
        _page = u"%s:%s:%s" % (page._site.family.name, page._site.lang, page._title)
        if _page not in seenPages:
            seenPages[_page] = True
            yield page

def RegexFilterPageGenerator(generator, regex):
    """
    Wraps around another generator. Yields only those pages, the titles of
    which are positively matched to regex.
    """
    reg = re.compile(regex, re.I)

    for page in generator:
        if reg.match(page.titleWithoutNamespace()):
            yield page

def CombinedPageGenerator(generators):
    """
    Wraps around a list of other generators. Yields all pages generated by
    the first generator; when the first generator stops yielding pages,
    yields those generated by the second generator, etc.
    """
    for generator in generators:
        for page in generator:
            yield page

def CategoryGenerator(generator):
    """
    Wraps around another generator. Yields the same pages, but as Category
    objects instead of Page objects. Makes sense only if it is ascertained
    that only categories are being retrieved.
    """
    for page in generator:
        yield catlib.Category(page.site(), page.title())

def PageWithTalkPageGenerator(generator):
    """
    Wraps around another generator. Yields the same pages, but for non-talk
    pages, it also includes associated talk pages.
    This generator does not check if the talk page in fact exists.
    """
    for page in generator:
        yield page
        if not page.isTalkPage():
            yield page.toggleTalkPage()


class PreloadingGenerator(object):
    """
    Yields the same pages as generator generator. Retrieves 60 pages (or
    another number specified by pageNumber), loads them using
    Special:Export, and yields them one after the other. Then retrieves more
    pages, etc. Thus, it is not necessary to load each page separately.
    Operates asynchronously, so the next batch of pages is loaded in the
    background before the first batch is fully consumed.
    """
    def __init__(self, generator, pageNumber=60, lookahead=10):
        self.wrapped_gen = generator
        self.pageNumber = pageNumber
#        ThreadedGenerator.__init__(self, name="Preloading-Thread",
#                                   qsize=lookahead)

    def __iter__(self):
        try:
            # this array will contain up to pageNumber pages and will be flushed
            # after these pages have been preloaded and yielded.
            somePages = []
            for page in self.wrapped_gen:
##                if self.finished.isSet():
##                    return
                somePages.append(page)
                # We don't want to load too many pages at once using XML export.
                # We only get a maximum number at a time.
                if len(somePages) >= self.pageNumber:
                    for loaded_page in self.preload(somePages):
                        yield loaded_page
                    somePages = []
            if somePages:
                # wrapped generator is exhausted but some pages still unloaded
                # preload remaining pages
                for loaded_page in self.preload(somePages):
                    yield loaded_page
        except GeneratorExit:
            pass
        except Exception, e:
            traceback.print_exc()
            wikipedia.output(unicode(e))

    def preload(self, page_list, retry=False):
        try:
            while len(page_list) > 0:
                # It might be that the pages are on different sites,
                # e.g. because the -interwiki parameter was used.
                # Query the sites one by one.
                site = page_list[0].site()
                pagesThisSite = [page for page in page_list
                                      if page.site() == site]
                page_list = [page for page in page_list
                                  if page.site() != site]
                wikipedia.getall(site, pagesThisSite)
                for page in pagesThisSite:
                    yield page
        except IndexError:
            # Can happen if the pages list is empty. Don't care.
            pass
        except wikipedia.SaxError:
            if not retry:
                # Retry once.
                self.preload(page_list, retry=True)
            # Ignore this error, and get the pages the traditional way later.
            pass


class GeneratorFactory:
    """
    This factory is responsible for processing command line arguments
    that are used by many scripts and that determine which pages
    to work on.
    """
    def __init__(self):
        self.gens = []
        self.namespaces = []

    """
    This method returns the combination the given generator and all
    accumulated generators that have been created in the process of handling
    arguments.

    Only call this method after all arguments have been parsed.
    """
    def getCombinedGenerator(self, gen = None):
        if gen:
            self.gens.insert(0, gen)
        if (len(self.gens) == 0):
            return None
        if (len(self.gens) == 1):
            gensList = self.gens[0]
        else:
            gensList = CombinedPageGenerator(self.gens)
        genToReturn = DuplicateFilterPageGenerator(gensList)
        if (self.namespaces):
            genToReturn = NamespaceFilterPageGenerator(genToReturn, map(int, self.namespaces))
        return genToReturn

    def getCategoryGen(self, arg, length, recurse = False):
        site = wikipedia.getSite()
        if len(arg) == length:
            categoryname = wikipedia.input(u'Please enter the category name:')
        else:
            categoryname = arg[length + 1:]

        ind = categoryname.find('|')
        startfrom = None
        if ind > 0:
            startfrom = categoryname[ind + 1:]
            categoryname = categoryname[:ind]

        cat = catlib.Category(site,
                              "%s:%s" % (site.namespace(14), categoryname))
        return CategorizedPageGenerator(cat, start=startfrom, recurse=recurse)

    def setSubCategoriesGen(self, arg, length, recurse = False):
        site = wikipedia.getSite()
        if len(arg) == length:
            categoryname = wikipedia.input(u'Please enter the category name:')
        else:
            categoryname = arg[length + 1:]

        ind = categoryname.find('|')
        if ind > 0:
            startfrom = categoryname[ind + 1:]
            categoryname = categoryname[:ind]
        else:
            startfrom = None

        cat = catlib.Category(site,
                              "%s:%s" % (site.namespace(14), categoryname))
        return SubCategoriesPageGenerator(cat, start=startfrom, recurse=recurse)

    def handleArg(self, arg):
        """Parse one argument at a time.

        If it is recognized as an argument that specifies a generator, a
        generator is created and added to the accumulation list, and the
        function returns true.  Otherwise, it returns false, so that caller
        can try parsing the argument. Call getCombinedGenerator() after all
        arguments have been parsed to get the final output generator.

        """
        site = wikipedia.getSite()
        gen = None
        if arg.startswith('-filelinks'):
            fileLinksPageTitle = arg[11:]
            if not fileLinksPageTitle:
                fileLinksPageTitle = wikipedia.input(
                    u'Links to which image page should be processed?')
            if fileLinksPageTitle.startswith(site.namespace(6)
                                             + ":"):
                fileLinksPage = wikipedia.ImagePage(site,
                                                    fileLinksPageTitle)
            else:
                fileLinksPage = wikipedia.ImagePage(site,
                                                'Image:' + fileLinksPageTitle)
            gen = FileLinksGenerator(fileLinksPage)
        elif arg.startswith('-unusedfiles'):
            if len(arg) == 12:
                gen = UnusedFilesGenerator()
            else:
                gen = UnusedFilesGenerator(number = int(arg[13:]))
        elif arg.startswith('-unwatched'):
            if len(arg) == 10:
                gen = UnwatchedPagesPageGenerator()
            else:
                gen = UnwatchedPagesPageGenerator(number = int(arg[11:]))
        elif arg.startswith('-usercontribs'):
            gen = UserContributionsGenerator(arg[14:])
        elif arg.startswith('-withoutinterwiki'):
            if len(arg) == 17:
                gen = WithoutInterwikiPageGenerator()
            else:
                gen = WithoutInterwikiPageGenerator(number = int(arg[18:]))
        elif arg.startswith('-interwiki'):
            title = arg[11:]
            if not title:
                title = wikipedia.input(u'Which page should be processed?')
            page = wikipedia.Page(site, title)
            gen = InterwikiPageGenerator(page)
        elif arg.startswith('-randomredirect'):
            if len(arg) == 15:
                gen = RandomRedirectPageGenerator()
            else:
                gen = RandomRedirectPageGenerator(number = int(arg[16:]))
        elif arg.startswith('-random'):
            if len(arg) == 7:
                gen = RandomPageGenerator()
            else:
                gen = RandomPageGenerator(number = int(arg[8:]))
        elif arg.startswith('-recentchanges'):
            if len(arg) == 14:
                gen = RecentchangesPageGenerator()
            else:
                gen = RecentchangesPageGenerator(number = int(arg[15:]))
        elif arg.startswith('-file'):
            textfilename = arg[6:]
            if not textfilename:
                textfilename = wikipedia.input(
                    u'Please enter the local file name:')
            gen = TextfilePageGenerator(textfilename)
        elif arg.startswith('-namespace'):
            if len(arg) == len('-namespace'):
                self.namespaces.append(wikipedia.input(u'What namespace are you filtering on?'))
            else:
                self.namespaces.extend(arg[len('-namespace:'):].split(","))
            return True
        elif arg.startswith('-catr'):
            gen = self.getCategoryGen(arg, len('-catr'), recurse = True)
        elif arg.startswith('-category'):
            gen = self.getCategoryGen(arg, len('-category'))
        elif arg.startswith('-cat'):
            gen = self.getCategoryGen(arg, len('-cat'))
        elif arg.startswith('-subcatsr'):
            gen = self.setSubCategoriesGen(arg, 9, recurse = True)
        elif arg.startswith('-subcats'):
            gen = self.setSubCategoriesGen(arg, 8)
        # This parameter is deprecated, catr should be used instead.
        elif arg.startswith('-subcat'):
            gen = self.getCategoryGen(arg, 7, recurse = True)
        elif arg.startswith('-page'):
            if len(arg) == len('-page'):
                gen = [wikipedia.Page(site,
                                      wikipedia.input(
                                          u'What page do you want to use?'))]
            else:
                gen = [wikipedia.Page(site, arg[len('-page:'):])]
        elif arg.startswith('-uncatfiles'):
            gen = UnCategorizedImageGenerator()
        elif arg.startswith('-uncatcat'):
            gen = UnCategorizedCategoryGenerator()
        elif arg.startswith('-uncat'):
            gen = UnCategorizedPageGenerator()
        elif arg.startswith('-ref'):
            referredPageTitle = arg[5:]
            if not referredPageTitle:
                referredPageTitle = wikipedia.input(
                    u'Links to which page should be processed?')
            referredPage = wikipedia.Page(site, referredPageTitle)
            gen = ReferringPageGenerator(referredPage)
        elif arg.startswith('-links'):
            linkingPageTitle = arg[7:]
            if not linkingPageTitle:
                linkingPageTitle = wikipedia.input(
                    u'Links from which page should be processed?')
            linkingPage = wikipedia.Page(site, linkingPageTitle)
            gen = LinkedPageGenerator(linkingPage)
        elif arg.startswith('-weblink'):
            url = arg[9:]
            if not url:
                url = wikipedia.input(
                    u'Pages with which weblink should be processed?')
            gen = LinksearchPageGenerator(url)
        elif arg.startswith('-transcludes'):
            transclusionPageTitle = arg[len('-transcludes:'):]
            if not transclusionPageTitle:
                transclusionPageTitle = wikipedia.input(
                    u'Pages that transclude which page should be processed?')
            transclusionPage = wikipedia.Page(site,
                                   "%s:%s" % (site.namespace(10),
                                              transclusionPageTitle))
            gen = ReferringPageGenerator(transclusionPage,
                                         onlyTemplateInclusion=True)
        elif arg.startswith('-gorandom'):
            for firstPage in RandomPageGenerator(number = 1):
                firstPageTitle = firstPage.title()
            namespace = wikipedia.Page(site, firstPageTitle).namespace()
            firstPageTitle = wikipedia.Page(site,
                                 firstPageTitle).titleWithoutNamespace()
            gen = AllpagesPageGenerator(firstPageTitle, namespace,
                                        includeredirects=False)
        elif arg.startswith('-start'):
            if arg.startswith('-startxml'):
                wikipedia.output(u'-startxml : wrong parameter')
                sys.exit()
            firstPageTitle = arg[7:]
            if not firstPageTitle:
                firstPageTitle = wikipedia.input(
                    u'At which page do you want to start?')
            namespace = wikipedia.Page(site, firstPageTitle).namespace()
            firstPageTitle = wikipedia.Page(site,
                                 firstPageTitle).titleWithoutNamespace()
            gen = AllpagesPageGenerator(firstPageTitle, namespace,
                                        includeredirects=False)
        elif arg.startswith('-prefixindex'):
            prefix = arg[13:]
            namespace = None
            if not prefix:
                prefix = wikipedia.input(
                    u'What page names are you looking for?')
            gen = PrefixingPageGenerator(prefix = prefix)
        elif arg.startswith('-newimages'):
            limit = arg[11:] or wikipedia.input(
                u'How many images do you want to load?')
            gen = NewimagesPageGenerator(number = int(limit))
        elif arg.startswith('-new'):
            if len(arg) >=5:
              gen = NewpagesPageGenerator(number = int(arg[5:]))
            else:
              gen = NewpagesPageGenerator(number = 60)
        elif arg.startswith('-imagelinks'):
            imagelinkstitle = arg[len('-imagelinks:'):]
            if not imagelinkstitle:
                imagelinkstitle = wikipedia.input(
                    u'Images on which page should be processed?')
            imagelinksPage = wikipedia.Page(site, imagelinkstitle)
            gen = ImagesPageGenerator(imagelinksPage)
        elif arg.startswith('-search'):
            mediawikiQuery = arg[8:]
            if not mediawikiQuery:
                mediawikiQuery = wikipedia.input(
                    u'What do you want to search for?')
            # In order to be useful, all namespaces are required
            gen = SearchPageGenerator(mediawikiQuery, namespaces = [])
        elif arg.startswith('-google'):
            gen = GoogleSearchPageGenerator(arg[8:])
        elif arg.startswith('-titleregex'):
            if len(arg) == 6:
                regex = wikipedia.input(u'What page names are you looking for?')
            else:
                regex = arg[7:]
            gen = RegexFilterPageGenerator(site.allpages(), regex)
        elif arg.startswith('-yahoo'):
            gen = YahooSearchPageGenerator(arg[7:])
        else:
            pass
        if gen:
            self.gens.append(gen)
            return self.getCombinedGenerator()
        else:
            return False

if __name__ == "__main__":
    try:
        genFactory = GeneratorFactory()
        for arg in wikipedia.handleArgs():
            if not genFactory.handleArg(arg):
                wikipedia.showHelp('pagegenerators')
                break
        else:
            gen = genFactory.getCombinedGenerator()
            if gen:
                for page in gen:
                    wikipedia.output(page.title(), toStdout = True)
            else:
                wikipedia.showHelp('pagegenerators')
    finally:
        wikipedia.stopme()
