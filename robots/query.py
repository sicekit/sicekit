#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This module allow you to use the API in a simple and easy way.


-- Example --

    params = {
        'action'    :'query',
        'prop'      :'revisions',
        'titles'    :'Test',
        'rvlimit'   :'2',
        'rvprop'    :'user|timestamp|content',
        }

    print query.GetData(params,
                        useAPI = True, encodeTitle = False)

"""
#
# (C) Yuri Astrakhan, 2006
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: query.py 7078 2009-07-18 17:41:49Z alexsh $'
#

import wikipedia, simplejson, urllib, time

def GetData(params, site = None, verbose = False, useAPI = False, retryCount = 5, encodeTitle = True):
    """Get data from the query api, and convert it into a data object
    """
    if site is None:
        site = wikipedia.getSite()

    for k,v in params.iteritems():
        if not IsString(v):
            params[k] = unicode(v)

    params['format'] = 'json'

    if not useAPI:
        params['noprofile'] = ''

    for k,v in params.iteritems():
        if type(v) == type(u''):
            params[k] = ToUtf8(v)

    # Titles param might be long, case convert it to post request
    data = None
    titlecount = 0
    if 'titles' in params:
        titlecount = params['titles'].count('|')
        if encodeTitle:
            data = {'titles' : params['titles']}
            del params['titles']

    postAC = [
        'edit', 'login', 'purge', 'rollback', 'delete', 'undelete', 'protect',
        'block', 'unblock', 'move', 'emailuser','import', 'userrights',
    ]
    if useAPI:
        if params['action'] in postAC:
            path = site.api_address()
        else:
            path = site.api_address() + urllib.urlencode(params.items())

    else:
        path = site.query_address() + urllib.urlencode(params.items())

    if verbose:
        if titlecount > 0:
            wikipedia.output(u"Requesting %d titles from %s:%s" % (titlecount, site.lang, path))
        else:
            wikipedia.output(u"Request %s:%s" % (site.lang, path))

    lastError = None
    retry_idle_time = 5

    while retryCount >= 0:
        try:
            jsontext = "Nothing received"
            if params['action'] in postAC:
                res, jsontext = site.postData(path, urllib.urlencode(params.items()), cookies=site.cookies())
            else:
                jsontext = site.getUrl( path, retry=True, data=data )

            # This will also work, but all unicode strings will need to be converted from \u notation
            # decodedObj = eval( jsontext )
            return simplejson.loads( jsontext )

        except ValueError, error:
            retryCount -= 1
            wikipedia.output(u"Error downloading data: %s" % error)
            wikipedia.output(u"Request %s:%s" % (site.lang, path))
            wikipedia.debugDump('ApiGetDataParse', site, str(error) + '\n%s' % path, jsontext)
            lastError = error
            if retryCount >= 0:
                wikipedia.output(u"Retrying in %i seconds..." % retry_idle_time)
                time.sleep(retry_idle_time)
                # Next time wait longer, but not longer than half an hour
                retry_idle_time *= 2
                if retry_idle_time > 300:
                    retry_idle_time = 300


    raise lastError

def GetInterwikies(site, titles, extraParams = None ):
    """ Usage example: data = GetInterwikies('ru','user:yurik')
    titles may be either ane title (as a string), or a list of strings
    extraParams if given must be a dict() as taken by GetData()
    """

    params = {'titles':ListToParam(titles), 'what' : 'redirects|langlinks'}
    params = CombineParams( params, extraParams )
    return GetData(site, params )

def GetLinks(site, titles, extraParams = None ):
    """ Get list of templates for the given titles
    """
    params = {'titles':ListToParam(titles), 'what': 'redirects|links'}
    params = CombineParams( params, extraParams )
    return GetData(site, params )

def GetDisambigTemplates(site):
    """This method will return a set of disambiguation templates.
    Template:Disambig is always assumed to be default, and will be
    appended (in localized format) regardless of its existence.
    The rest will be aquired from the Wikipedia:Disambiguation Templates page.
    Only links to templates will be used from that page.
    """

    disambigs = set()
    disambigName = u"template:disambig"
    disListName = u"Wikipedia:Disambiguation Templates"
    disListId = 0

    templateNames = GetLinks(site, [disListName, disambigName])
    for id, page in templateNames['pages'].iteritems():
        if page['title'] == disambigName:
            if 'normalizedTitle' in page:
                disambigs.add(page['normalizedTitle'])
            elif 'redirect' in page:
                disambigs.add(page['title'])
        elif page['title'] == disListName:
            if 'normalizedTitle' in page:
                if 'refid' in page:
                    disListId = page['refid']
            else:
                disListId = id

    # Disambig page was found
    if disListId > 0:
        page = templateNames['pages'][disListId]
        if 'links' in page:
            for l in page['links']:
                if l['ns'] == 10:
                    disambigs.add(l['*'])

    return disambigs
#
#
# Helper utilities
#
#

def CleanParams( params ):
    """Params may be either a tuple, a list of tuples or a dictionary.
    This method will convert it into a dictionary
    """
    if params is None:
        return dict()
    pt = type( params )
    if pt == type( {} ):
        return params
    elif pt == type( () ):
        if len( params ) != 2: raise "Tuple size must be 2"
        return {params[0]:params[1]}
    elif pt == type( [] ):
        for p in params:
            if p != type( () ) or len( p ) != 2: raise "Every list element must be a 2 item tuple"
        return dict( params )
    else:
        raise "Unknown param type %s" % pt

def CombineParams( params1, params2 ):
    """Merge two dictionaries. If they have the same keys, their values will
    be appended one after another separated by the '|' symbol.
    """

    params1 = CleanParams( params1 )
    if params2 is None:
        return params1
    params2 = CleanParams( params2 )

    for k, v2 in params2.iteritems():
        if k in params1:
            v1 = params1[k]
            if len( v1 ) == 0:
                params1[k] = v2
            elif len( v2 ) > 0:
                if type('') != type(v1) or type('') != type(v2):
                    raise "Both merged values must be of type 'str'"
                params1[k] = v1 + '|' + v2
            # else ignore
        else:
            params1[k] = v2
    return params1

def ConvToList( item ):
    """Ensure the output is a list
    """
    if item is None:
        return []
    elif IsString(item):
        return [item]
    else:
        return item

def ListToParam( list ):
    """Convert a list of unicode strings into a UTF8 string separated by the '|' symbols
    """
    list = ConvToList( list )
    if len(list) == 0:
        return ''

    encList = ''
    # items may not have one symbol - '|'
    for l in list:
        if '|' in l: raise "item '%s' contains '|' symbol" % l
        encList += ToUtf8(l) + '|'
    return encList[:-1]

def ToUtf8(s):
    if type(s) != type(u''):
        wikipedia.output("item %s is not unicode" % unicode(s))
        raise
    return s.encode('utf-8')

def IsString(s):
    return type( s ) in [type( '' ), type( u'' )]
