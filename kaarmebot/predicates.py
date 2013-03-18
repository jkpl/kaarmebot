import re
import functools as f


class Predicate(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.setup()

    def __call__(self, matchable):
        return self.match(matchable)

    def setup(self):
        pass

    def match(self, matchable):
        raise NotImplemented()


class All(Predicate):
    def match(self, matchable):
        for predicate in self.args:
            if not predicate(matchable):
                return False
        return True


class Any(Predicate):
    def match(self, matchable):
        for predicate in self.args:
            if predicate(matchable):
                return True
        return False


class Equals(Predicate):
    def match(self, matchable):
        return matchable == self.args[0]


class AttrIn(Predicate):
    def setup(self):
        self.return_bool = self.kwargs.get('return_bool', False)

    def match(self, matchable):
        attr_value = getattr(matchable, self.args[0], None)
        targets = self.args[1:]
        if attr_value is not None and attr_value in targets:
            if self.return_bool:
                return True
            return attr_value
        return False


class MatchAttribute(Predicate):
    def match(self, matchable):
        attr_value = getattr(matchable, self.args[0], None)
        predicate = self.args[1]
        return predicate(attr_value)


class RegEx(Predicate):
    def setup(self):
        self.reprog = re.compile(self.args[0])
        self.attr = self.kwargs.get('attr')

    def match(self, matchable):
        if self.attr:
            target = getattr(matchable, self.attr, '')
        else:
            target = matchable
        return self.reprog.match(target)


# Messaging specific
OnContents = f.partial(MatchAttribute, 'contents')
ClientStarted = OnContents(Equals('started'))


# IRC specific
def Command(*args, **kwargs):
    return OnContents(AttrIn('command', *args, **kwargs))


def Name(*args, **kwargs):
    return OnContents(AttrIn('name', *args, **kwargs))


BodyRegEx = lambda regex: OnContents(RegEx(regex, attr='body'))
Ping = Command('PING')
PrivMsg = Command('PRIVMSG')
Connected = Command('001')
