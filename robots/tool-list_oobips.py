#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This bot regenerates the page VEIDs

The following parameters are supported:

    -debug         If given, doesn't do any real changes, but only shows
                   what would have been changed.

"""
__version__ = '$Id: basic.py 4946 2008-01-29 14:58:25Z wikipedian $'
import wikipedia
import pagegenerators, catlib


class OOBIPBot:
    # Edit summary message that should be used.
    # NOTE: Put a good description here, and add translations, if possible!
    msg = {
        'en': u'Robot: regenerated list.',
    }

    def __init__(self, generator, debug):
        """
        Constructor. Parameters:
            * generator - The page generator that determines on which pages
                          to work on.
            * debug     - If True, doesn't do any real changes, but only shows
                          what would have been changed.
        """
        self.generator = generator
        self.debug = debug

    def run(self):
        # Set the edit summary message
        for page in self.generator:
            self.treat(page)


    def treat(self, page):
        """
        Loads the given page, does some changes, and saves it.
        """
        try:
            # Load the page
            text = page.get()
        except wikipedia.NoPage:
            wikipedia.output(u"Page %s does not exist; skipping." % page.aslink())
            return
        except wikipedia.IsRedirectPage:
            wikipedia.output(u"Page %s is a redirect; skipping." % page.aslink())
            return

        # save veid into list
        for line in text.split("\n"):
          if not line.startswith("|OOBIP"): continue
          (junk, ip) = line.split("=")
	  #print "%s: %s" % (page.urlname(), repr(veid))
          print ip

def main():
    # The generator gives the pages that should be worked upon.
    gen = None
    # If debug is True, doesn't do any real changes, but only show
    # what would have been changed.
    debug = False
    wantHelp = False

    cat = catlib.Category(wikipedia.getSite(), 'Category:%s' % 'HP ILO2')
    gen = pagegenerators.CategorizedPageGenerator(cat, start = None, recurse = False)

    # Parse command line arguments
    for arg in wikipedia.handleArgs():
        if arg.startswith("-debug"):
            debug = True
        else:
            print arg, "yielding wanthelp"
            wantHelp = True

    if not wantHelp:
        # The preloading generator is responsible for downloading multiple
        # pages from the wiki simultaneously.
        gen = pagegenerators.PreloadingGenerator(gen)
        bot = OOBIPBot(gen, debug)
        bot.run()
    else:
        wikipedia.showHelp()

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
