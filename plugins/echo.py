class Echo:
    def __init__(self, settings):
        self.settings = settings

    def setup(self):
        print "Echo plugin setup"

    def pubmsg(self, target, source, msg=None):
        if msg:
            return {'privmsg': (target,'"%s"' % msg)}
        return None
