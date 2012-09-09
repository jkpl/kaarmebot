from kaarmebot import BotApp
import example_plugin
import json

app_conf = {
    'channels': {
        'irc.server.net': ["#somechannel", "#someotherchannel"]
    },
    'servers': [
        ('irc.server.net', 6667, 'secretpassword')
    ],
    'nickname': 'BotName',
    'real_name': 'Sir Bot McBotsworth, Esq.'
}

plugin_bindings = [
    ('{nick}, {msg}', 'echo1'),
    ('{nick}: {msg}', 'echo2'),
    ('.*https?://[.\w]*youtube\.com/watch\?(?P<path>[^\s]+).*', 'utube'),
    ('.*https?://youtu\.be/(?P<vid>[^\s]+).*', 'utube'),
]

if __name__ == '__main__':
    with open('example.json') as f:
        app_conf.update(json.loads(f.read()))

    app = BotApp(**app_conf)
    app.scan(example_plugin)
    for pattern, name in plugin_bindings:
        app.add_binding(pattern, name)
    app.start()
