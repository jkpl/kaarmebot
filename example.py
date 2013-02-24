#!/usr/bin/env python
# -*- coding: utf-8 -*-

from kaarmebot import BotApp
from kaarmebot import predicates as p
import example_plugin

app_conf = {
    'servers': {
        ('someserver.com', 6667): {
            'real_name': 'Sir Bot McBotsworth, Esq.',
            'nick': 'BotName',
            'username': 'botname',
            'channels': ('#something',)
        }
    }
}

plugin_bindings = [
     (p.All(p.PrivMsg, p.BodyRegEx('(?P<nick>.*): (?P<msg>.*)')), 'echo'),
     (p.All(p.PrivMsg,
            p.BodyRegEx('.*https?://[.\w]*youtube\.com/watch\?[^\s]+.*')),
      'utube'),
     (p.All(p.PrivMsg,
            p.BodyRegEx('.*https?://youtu\.be/[^\s]+.*')),
      'utube'),
]

if __name__ == '__main__':
    app = BotApp(app_conf)
    app.scan(example_plugin)
    for predicate, name in plugin_bindings:
        app.add_binding(predicate, name)
    app.start()
