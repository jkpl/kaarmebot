import re
import json
from kaarmebot.plugin import plugin_config
from kaarmebot import irc
from urllib import urlopen
from urlparse import parse_qs


@plugin_config(name="echo")
def echo_to_source(request):
    message = request.message
    d = re.match('(?P<nick>.*): (?P<msg>.*)', message.body).groupdict()
    msg = d.get('msg')
    own_nick = d.get('nick')
    target = message.parameters[0]
    source = irc.string_to_person(message.name).nick
    if msg:
        if target != own_nick:
            return irc.privmsg(target, "%s: %s" % (source, msg))
        else:
            return irc.privmsg(source, "%s: %s" % (source, msg))
    return None


@plugin_config(name="utube")
def utube(request):
    message = request.message
    target = message.parameters[0]
    vid = get_youtube_video_id_from_url(message.body)
    if vid:
        url = ''.join(('https://gdata.youtube.com/feeds/api/videos/',
                       vid, '?v=2&alt=json'))
        res = urlopen(url).read()
        d = json.loads(res)
        title = d['entry']['title']['$t']
        return irc.privmsg(target, "YouTube: %s" % title)
    return None


def get_youtube_video_id_from_url(contents):
    short_url_match = re.match('.*https?://youtu\.be/(?P<vid>[^\s]+).*',
                               contents)
    if short_url_match:
        return short_url_match.groupdict().get('vid')

    long_url_match = re.match(
        '.*https?://[.\w]*youtube\.com/watch\?(?P<path>[^\s]+).*',
        contents)

    if long_url_match:
        return parse_qs(long_url_match.groupdict().get('path', '')).get('v')[0]

    return None
