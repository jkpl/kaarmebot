import types
import logging
from gevent import monkey; monkey.patch_all()
from ircbot import SingleServerIRCBot
from collections import namedtuple


logger = logging.getLogger(__name__)


IrcMsg = namedtuple("IrcMsg", ['msgtype', 'message', 'target', 'source',
                               'own_nick'])


class BotCore(SingleServerIRCBot):
    def __init__(self, channels, servers, nickname, real_name, msgcallback):
        SingleServerIRCBot.__init__(self, servers, nickname, real_name)
        self.channeld = channels
        self.msgcallback = msgcallback
        self.connection.add_global_handler("all_events",
                                           self._message_dispatch, -10)

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        channels = self.channeld.get(c.server)
        if channels:
            for chan in channels:
                c.join(chan)

    def _message_dispatch(self, c, e):
        def _execute_callback(data):
            try:
                it = data.iteritems() if isinstance(data, dict) else data
                for funname, arglist in it:
                    for args in arglist:
                        getattr(c, funname)(*args)
            except:
                logger.exception("Error occurred when executing return data.")

        args = e.arguments()
        message = IrcMsg(msgtype=e.eventtype(), message=args,
                         target=e.target(), source=e.source(),
                         own_nick=c.get_nickname())
        matchstr = ' '.join(args)
        self.msgcallback(_execute_callback, matchstr, message)
