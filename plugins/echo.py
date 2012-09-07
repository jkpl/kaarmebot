class Echo:
    def __init__(self, settings):
        self.settings = settings

    def setup(self):
        print "Echo plugin setup"

    def pubmsg(self, connection, target, source, msg=None):
        if msg:
            connection.privmsg(target, '"%s"' % msg)
