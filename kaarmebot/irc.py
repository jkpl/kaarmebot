import re
from collections import namedtuple


## Data structures
IrcMessage = namedtuple('IrcMsg', ['name', 'command', 'parameters',
                                   'body', 'raw'])
Person = namedtuple('Host', ['nick', 'username', 'hostname', 'full'])


## Commands
def any_command(*args, **kwargs):
    if len(args) == 1 and not kwargs:
        return args[0]
    else:
        return raw_command(*args, **kwargs)


def join(channels_and_passwords):
    channels, passwords = unzip_to_n_lists(channels_and_passwords,
                                           lists=2, padding_item='')
    channels_joined = ','.join(channels)
    passwords_joined = ','.join(passwords)
    return raw_command('JOIN', (channels_joined, passwords_joined))


def kick(channel, nick, reason=None):
    return raw_command('KICK', (channel, nick), reason)


def mode(channel, *args):
    mode_args = (channel,) + args
    return raw_command('MODE', mode_args)


def names(*channels):
    channels_joined = ','.join(channels) if channels else None
    return raw_command('NAMES', channels_joined)


def nick(user_nick):
    return raw_command('NICK', user_nick)


def part(*channels):
    channels_joined = ','.join(channels) if channels else None
    return raw_command('PART', channels_joined)


def password(password):
    return raw_command('PASS', password)


def privmsg(target, message):
    return raw_command('PRIVMSG', target, message)


def pong(name):
    return raw_command('PONG', body=name)


def quit(message=None):
    return raw_command('QUIT', body=message)


def raw_command(command, parameters=None, body=None):
    cmd = [to_unicode(command.upper())]
    if parameters:
        if type(parameters) in (list, tuple):
            p = [to_unicode(x) for x in parameters if x]
            cmd.append(' '.join(p))
        else:
            cmd.append(to_unicode(parameters))
    if body:
        cmd.append(':' + to_unicode(body))
    return ' '.join(cmd)


def topic(channel, new_topic=None):
    return raw_command('TOPIC', channel, new_topic)


def user(username, usermode, real_name):
    return raw_command('USER', (username, usermode, '*'), real_name)


## Message parsing
def parse_message(message):
    decoded = to_unicode(message).translate('\r\n')
    first, rest = pick_first_part(decoded)
    if first[0] == ':':
        name = first[1:]
        command, rest = pick_first_part(rest)
        parameters, body = pick_first_part(rest, ':')
        parameters = [x for x in parameters.split(' ') if x]
        return IrcMessage(name, command, parameters, body, decoded)
    else:
        _, rest = pick_first_part(rest, ':')
        return IrcMessage(None, first, None, rest, decoded)


def pick_first_part(message, delimeter=' '):
    if message:
        splitted = message.split(delimeter, 1)
        first = splitted[0]
        rest = ' '.join(splitted[1:]) or None
        return (first, rest)
    return (None, None)


## Helpers
def unzip_to_n_lists(sequence, lists=2, padding_item=None):
    unzip_lists = [list() for _ in xrange(lists)]
    for item in sequence:
        if type(item) in (list, tuple):
            append_items_to_list(item, unzip_lists, padding_item)
        else:
            unzip_lists[0].append(item)
            for x in xrange(1, lists):
                unzip_lists[x].append(padding_item)
    return unzip_lists


def append_items_to_list(from_sequence, to_lists, padding_item=None):
    for x in xrange(len(to_lists)):
        to_lists[x].append(get_or_none(from_sequence, x) or padding_item)


def get_or_none(collection, key):
    try:
        return collection[key]
    except (IndexError, KeyError) as e:
        return None


def to_unicode(obj):
    return (obj.decode('utf-8', 'replace')
            if isinstance(obj, basestring) else unicode(obj))


def string_to_person(person_str):
    m = re.match('(.*)!(.*)@(.*)', person_str)
    return Person(m.group(1), m.group(2), m.group(3), person_str)
