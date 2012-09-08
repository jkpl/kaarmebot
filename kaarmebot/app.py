#!/usr/bin/env python
# -*- coding: utf-8 -*-

import types
import venusian
from multiprocessing import Pool
from botcore import BotCore
from dispatcher import MessageDispatcher, execute_handler


class plugin_config:
    def __init__(self, **settings):
        self.__dict__.update(settings)

    def __call__(self, wrapped):
        settings = self.__dict__.copy()

        def callback(scanner, name, ob):
            if settings.get('name') is None:
                settings['name'] = name
            scanner.add_plugin(ob, **settings)

        info = venusian.attach(wrapped, callback, category='plugins')
        if info.scope == 'class' and settings.get('attr') is None:
            settings['attr'] = wrapped.__name__

        return wrapped


class BotApp:
    def __init__(self, channels, servers, nickname, real_name, workers=4,
                 plugin_settings=None):
        self.plugins = {}
        self._pool = Pool(processes=workers)
        self.dispatcher = MessageDispatcher(plugin_settings)
        self.bot = BotCore(channels, servers, nickname, real_name,
                           self._message_callback)
        self._scanner = venusian.Scanner(add_plugin=self.add_plugin)

    def add_route(self, regex, name, msgtypes=None, attr=None):
        handler, settings = self.plugins[name]
        msgtypes = (tuple(msgtypes or []) +
                    tuple(settings.get('msgtypes', [])))
        attr = attr or settings.get('attr')
        self.dispatcher.add_route(regex, handler, msgtypes, attr)

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
