import sys

class SampleRobot:
  """The sample robot. Does nothing really useful."""

  def run(self, configuration, wiki):
    self.configuration = configuration
    self.wiki = wiki

    print 'hi!'
    print sys.argv
    print self.wiki

"""Main entry point from sicekit.wiki.robot.wrapper."""
RobotMain = SampleRobot().run

