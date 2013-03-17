from applogic import ClientStatusMessage
from plugin import plugin_config
import irc


@plugin_config(name='builtin_ping')
def ping(request):
    target = request.irc_message.body
    return irc.pong(target)


@plugin_config(name='builtin_after_connect_join')
def after_connect_join(request):
    channels = request.source_settings.get('channels')
    return irc.join(channels)


@plugin_config(name='builtin_init_connection',
               routing_class=ClientStatusMessage)
def init_connection(request):
    conf = request.source_settings

    username = conf.get('username')
    usermode = conf.get('usermode', 8)
    real_name = conf.get('real_name')
    password = conf.get('password')
    nick = conf.get('nick')

    commands = [irc.user(username, usermode, real_name), irc.nick(nick)]
    if password:
        commands.append(irc.password(password))

    return commands
