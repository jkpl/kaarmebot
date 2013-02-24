import unittest
from kaarmebot import irc


class TestIrcCommands(unittest.TestCase):
    def test_any_cmd(self):
        self.assertEquals('foobar', irc.any_cmd('foobar'))
        self.assertEquals(irc.raw_cmd('COMMAND', 'param', 'body'),
                          irc.any_cmd('COMMAND', 'param', 'body'))

    def test_join(self):
        channels = (('#foo', 'foo'), ('#bar', 'bar'), '#foobar')

        cmd = irc.join(channels)

        self.assertEquals('JOIN #foo,#bar,#foobar foo,bar,', cmd)

    def test_kick(self):
        self.assertEquals('KICK #foo bar :baz',
                          irc.kick('#foo', 'bar', 'baz'))
        self.assertEquals('KICK #foo bar',
                          irc.kick('#foo', 'bar'))

    def test_mode(self):
        self.assertEquals('MODE #foo +m',
                          irc.mode('#foo', '+m'))
        self.assertEquals('MODE #bar +o baz',
                          irc.mode('#bar', '+o', 'baz'))

    def test_names(self):
        self.assertEquals('NAMES #foobar',
                          irc.names('#foobar'))
        self.assertEquals('NAMES #foo,#bar',
                          irc.names('#foo', '#bar'))

    def test_nick(self):
        self.assertEquals('NICK kaarmebot',
                          irc.nick('kaarmebot'))

    def test_part(self):
        self.assertEquals('PART #foobar',
                          irc.part('#foobar'))
        self.assertEquals('PART #foo,#bar',
                          irc.part('#foo', '#bar'))

    def test_privmsg(self):
        self.assertEquals('PRIVMSG #foo :Bar',
                          irc.privmsg('#foo', 'Bar'))

    def test_pong(self):
        self.assertEquals('PONG :some.server.org',
                          irc.pong('some.server.org'))

    def test_quit(self):
        self.assertEquals('QUIT', irc.quit())
        self.assertEquals('QUIT :message',
                          irc.quit('message'))

    def test_raw_cmd(self):
        self.assertEquals('COMMAND param1 param2 :body_of_message',
                          irc.raw_cmd('COMMAND', ('param1', 'param2'),
                                      'body_of_message'))

    def test_topic(self):
        self.assertEquals('TOPIC #channel', irc.topic('#channel'))
        self.assertEquals('TOPIC #channel :some topic',
                          irc.topic('#channel', 'some topic'))

    def test_user(self):
        self.assertEquals('USER username mode * :Real Name',
                          irc.user('username', 'mode', 'Real Name'))


class TestIrcMessageParsing(unittest.TestCase):
    def setUp(self):
        self.name = 'somename'
        self.command = 'COMMAND'
        self.parameters = ('param1', 'param2')
        self.body = 'Message body'

    def test_normal_message(self):
        message1 = ':%s %s %s :%s' % (self.name, self.command,
                                      ' '.join(self.parameters), self.body)
        message2 = ':%s %s %s' % (self.name, self.command,
                                  ' '.join(self.parameters))
        message3 = ':%s %s :%s' % (self.name, self.command, self.body)

        ircmsg1 = irc.parse_message(message1)
        ircmsg2 = irc.parse_message(message2)
        ircmsg3 = irc.parse_message(message3)

        self.assertEquals(self.name, ircmsg1.name)
        self.assertEquals(self.name, ircmsg2.name)
        self.assertEquals(self.name, ircmsg3.name)
        self.assertEquals(self.command, ircmsg1.command)
        self.assertEquals(self.command, ircmsg2.command)
        self.assertEquals(self.command, ircmsg3.command)
        self.assertIn(self.parameters[0], ircmsg1.parameters)
        self.assertIn(self.parameters[1], ircmsg1.parameters)
        self.assertIn(self.parameters[0], ircmsg2.parameters)
        self.assertIn(self.parameters[1], ircmsg2.parameters)
        self.assertEquals(self.body, ircmsg1.body)
        self.assertEquals(self.body, ircmsg3.body)

    def test_special_message(self):
        message1 = '%s :%s' % (self.command, self.body)
        message2 = self.command

        ircmsg1 = irc.parse_message(message1)
        ircmsg2 = irc.parse_message(message2)

        self.assertEquals(self.command, ircmsg1.command)
        self.assertEquals(self.command, ircmsg2.command)
        self.assertEquals(self.body, ircmsg1.body)
