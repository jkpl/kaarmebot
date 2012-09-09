#!/usr/bin/env python
# -*- coding: utf-8 -*-

import types
import venusian
from multiprocessing import Pool
from botcore import BotCore
from dispatcher import MessageDispatcher, execute_handler


def plugin_config(**settings):
    def decorator(wrapped):
        sets = settings.copy()

        def callback(scanner, name, ob):
            if sets.get('name') is None:
                sets['name'] = name
            scanner.add_plugin(ob, **sets)

        info = venusian.attach(wrapped, callback, category='plugins')
        if info.scope == 'class' and sets.get('attr') is None:
            sets['attr'] = wrapped.__name__
        return wrapped
    return decorator


class BotApp:
    def __init__(self, channels, servers, nickname, real_name, workers=4,
                 plugin_settings=None):
        self.plugins = {}
        self._pool = Pool(processes=workers)
        self.dispatcher = MessageDispatcher(plugin_settings)
        self.bot = BotCore(channels, servers, nickname, real_name,
                           self._message_callback)
        self._scanner = venusian.Scanner(add_plugin=self.add_plugin)

    def add_binding(self, pattern, name, **moresettings):
        handler, settings = self.plugins[name]
        settings.update(moresettings)
        self.dispatcher.add_binding(pattern, handler, settings)

    def _message_callback(self, callback, *args):
        for handler_args in self.dispatcher.msg(*args):
            self._pool.apply_async(execute_handler, handler_args,
                                   callback=callback)

    def scan(self, module):
        self._scanner.scan(module)

    def add_plugin(self, handler, name, **settings):
        nid = settings.get('name') or name
        self.plugins[nid] = (handler, settings)

    def start(self):
        self.bot.start()
