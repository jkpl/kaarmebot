# -*- coding: utf-8 -*-

from ircbot import SingleServerIRCBot
import types


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
            for funname, arglist in data.iteritems():
                fun = getattr(c, funname, None)
                if fun_or_method(fun):
                    for args in arglist:
                        fun(*args)

        nick = c.get_nickname()
        metadata = {
            'target': e.target(),
            'source': e.source(),
            'own_nick': nick
        }
        args = e.arguments()
        msgtype = e.eventtype()
        self.msgcallback(msgtype, args, metadata, _execute_callback)


def fun_or_method(ob):
    return (isinstance(ob, types.FunctionType) or
            isinstance(ob, types.MethodType))
