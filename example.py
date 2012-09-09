from kaarmebot import BotApp
import example_plugin
import json

if __name__ == '__main__':
    conf = {
        'channels': {
            'irc.server.net': ["#somechannel", "#someotherchannel"]
        },
        'servers': [
            ('irc.server.net', 6667, 'secretpassword')
        ],
        'nickname': 'BotName',
        'real_name': 'Sir Bot McBotsworth, Esq.'
    }
    with open('example.json') as f:
        conf.update(json.loads(f.read()))
    app = BotApp(**conf)
    app.scan(example_plugin)
    app.add_binding("{nick}, {msg}", "echo1")
    app.add_binding("{nick}: {msg}", "echo2")
    app.add_binding(".*https?://[.\w]*youtube\.com/watch\?(?P<path>[^\s]+).*","utube")
    app.add_binding(".*https?://youtu\.be/(?P<vid>[^\s]+).*", "utube")
    app.start()
