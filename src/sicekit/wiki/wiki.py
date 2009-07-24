
from wikitools import wiki

class WikiLoginError(Exception):
  pass

def getWiki(configuration):
  """Create the wiki object from the configuration."""
  _wiki = wiki.Wiki(configuration.wiki_apiurl)
  _wiki.cookiepath = configuration.cookiejar
  if not _wiki.login(configuration.wiki_username, configuration.wiki_password, domain=configuration.wiki_domain, remember=True):
    raise WikiLoginError("Login failed early")
  if not _wiki.isLoggedIn():
    raise WikiLoginError("Login failed")
  return _wiki

