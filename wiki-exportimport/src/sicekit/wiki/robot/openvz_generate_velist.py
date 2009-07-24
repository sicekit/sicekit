from wikitools import category, page
from sicekit.wiki.wiki import getWiki

def RobotMain(configuration, wiki):
  return OpenvzGenerateVelistRobot(configuration, wiki).run()

class OpenvzGenerateVelistRobot:
  def __init__(self, configuration, wiki):
    self.configuration = configuration
    self.wiki = wiki
    self.companies = {10: 'IniTech', 20: 'ACME Corp.'} # FIXME: company-config file
    self.categoryname = 'VE'

  def collect_page_detail(self, page):
    # Load the page
    text = page.getWikiText()
    print text
    # save veid into list
    for line in text.split("\n"):
      if not line.startswith("|VEID"): continue
      (junk, veid) = line.split("=")
      self.veidlist[int(veid)] = page.urltitle

  def build_new_overviewpage_text(self):
    text = "<!-- Note: automatically generated by robot-generate_openvz_velist.py. -->\n"
    text += "[[VEID Naming Conventions]]\n\n"
    text += "=== Legacy IDs ===\n"
    keys = self.veidlist.keys()
    keys.sort()
    lastid = ""
    for id in keys:
      pagename = self.veidlist[id]
      id = str(id)
      companyid = id[0:2]
      if (not lastid.startswith(companyid)) and len(id) > 4:
        text += "=== " + companyid + " - " + self.companies[int(companyid)] + " ===\n"
      text += "* [[" + pagename + "|'''" + id + "''']]''':''' [[" + pagename + "]]\n"
      if len(id) > 4: lastid = id
    text += "[[Category:VE]]"
    return text

  def run(self):
    cat = category.Category(self.wiki, self.categoryname)
    self.overviewpage = page.Page(self.wiki, u"VEIDs")

    self.veidlist = {}
    for article in cat.getAllMembersGen(namespaces=[0]):
      self.collect_page_detail(article)

    try:
      oldtext = self.overviewpage.getWikiText()
    except page.NoPage:
      oldtext = ""

    newtext = self.build_new_overviewpage_text()
    # only save if something was changed
    if newtext == oldtext: return

    self.overviewpage.edit(text=newtext, skipmd5=True, bot=True,
      summary=u"Regenerated list.")
