#!/usr/bin/env python
# -*- coding: utf-8 -*-

import types
import venusian
from botcore import BotCore
from dispatcher import MessageDispatcher


class plugin_config:
    def __init__(self, **settings):
        self.__dict__.update(settings)

    def __call__(self, wrapped):
        settings = self.__dict__.copy()

        def callback(scanner, name, ob):
            scanner.add_plugin(ob, name, settings)

        info = venusian.attach(wrapped, callback, category='plugins')
        if info.scope == 'class' and settings.get('attr') is None:
            settings['attr'] = wrapped.__name__

        return wrapped


class BotApp:
    def __init__(self, channels, servers, nickname, real_name,
                 plugin_settings=None):
        self._plugins = {}
        self._scanner = venusian.Scanner(add_plugin=self._add_plugin)
        self.dispatcher = MessageDispatcher(plugin_settings)
        self.bot = BotCore(channels, servers, nickname, real_name,
                           self.dispatcher.msg)

    def add_route(self, regex, handler, msgtypes=None, attr=None):
        if isinstance(handler, basestring):
            handler, settings = self._plugins[handler]
            msgtypes = (tuple(msgtypes or []) +
                        tuple(settings.get('msgtypes', [])))
            attr = attr or settings.get('attr')
        self.dispatcher.add_route(regex, handler, msgtypes, attr)

    def scan(self, module):
        self._scanner.scan(module)

    def _add_plugin(self, handler, name, settings):
        name = settings.get('name') or name
        self._plugins[name] = (handler, settings)

    def start(self):
        self.bot.start()
