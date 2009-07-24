import sys

from optparse import OptionParser
from sicekit.configuration import getConfiguration
from sicekit.wiki.wiki import getWiki

class Wrapper(object):
  def __init__(self):
    pass

  def run(self, argv):
    if len(argv) < 2:
      print "Usage: sicekit-wiki-robot RobotName [options]"
      return 126

    robotname = "sicekit.wiki.robot.%s" % argv[1].lower()
    try:
      module = __import__(robotname, globals, locals, ['RobotMain'], 0)
    except:
      print "E: Robot %s could not be loaded (not found/syntax error?)" % robotname
      return 126

    if not getattr(module, 'RobotMain'):
      print "E: Robot %s has no RobotMain callable" % robotname
      return 126

    # prepare new sys.argv
    new_argv = [robotname]
    new_argv.extend(sys.argv[2:])
    sys.argv = new_argv

    configuration = getConfiguration()
    wiki = getWiki(configuration)

    # pass control to the robot
    module.RobotMain(configuration, wiki)
