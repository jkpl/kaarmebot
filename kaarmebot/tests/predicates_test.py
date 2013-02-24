import unittest
import re
import collections
from kaarmebot import predicates as p


TestTuple = collections.namedtuple('TestTuple', ['name', 'command', 'body'])


return_true = lambda _: True
return_false = lambda _: False
re_match_type = re.match('', '').__class__


def is_matchobj(obj):
    return isinstance(obj, re_match_type)


class TestPredicates(unittest.TestCase):
    test_var1 = 'SOME_NAME'
    test_var2 = 'SOME_OTHER_NAME'
    test_string1 = 'this is a test string'
    test_string2 = 'another test string'
    test_re1 = 'this.*'
    test_re2 = 'another.*'
    test_re3 = '.*string'
    tuple1 = TestTuple(test_var1, test_var1, test_string1)
    tuple2 = TestTuple(test_var2, test_var2, test_string2)

    def test_all_returns_true_if_all_predicates_return_true(self):
        predicate = p.All(return_true, return_true, return_true)

        self.assertTrue(predicate('something'))

    def test_all_returns_false_if_any_predicate_returns_false(self):
        predicate = p.All(return_true, return_false, return_true)

        self.assertFalse(predicate('something'))

    def test_any_returns_true_if_any_predicates_returns_true(self):
        predicate = p.Any(return_false, return_false, return_true)

        self.assertTrue(predicate('something'))

    def test_any_returns_false_if_all_predicates_return_false(self):
        predicate = p.Any(return_false, return_false, return_false)

        self.assertFalse(predicate('something'))

    def test_attrin_returns_attr_value_if_attr_is_any_of_given_values(self):
        predicate = p.AttrIn('name', self.test_var1, 'something_else')

        self.assertEquals(self.test_var1, predicate(self.tuple1))

    def test_attrin_returns_boolean_if_return_bool_is_set(self):
        predicate = p.AttrIn('name', self.test_var1, 'something_else',
                             return_bool=True)

        self.assertTrue(isinstance(predicate(self.tuple1), bool))
        self.assertTrue(isinstance(predicate(self.tuple2), bool))

    def test_attrin_returns_false_if_attr_is_none_of_given_values(self):
        predicate = p.AttrIn('name', self.test_var2, 'something')

        self.assertFalse(predicate(self.tuple1))

    def test_regex_returns_match_if_regex_matches(self):
        predicate1 = p.RegEx(self.test_re1)
        predicate2 = p.RegEx(self.test_re2)
        predicate3 = p.RegEx(self.test_re3)

        self.assertTrue(is_matchobj(predicate1(self.test_string1)))
        self.assertTrue(is_matchobj(predicate2(self.test_string2)))
        self.assertTrue(is_matchobj(predicate3(self.test_string1)))
        self.assertTrue(is_matchobj(predicate3(self.test_string2)))

    def test_regex_returns_match_if_regex_matches_attr(self):
        predicate1 = p.RegEx(self.test_re1, attr='body')
        predicate2 = p.RegEx(self.test_re2, attr='body')
        predicate3 = p.RegEx(self.test_re3, attr='body')

        self.assertTrue(is_matchobj(predicate1(self.tuple1)))
        self.assertTrue(is_matchobj(predicate2(self.tuple2)))
        self.assertTrue(is_matchobj(predicate3(self.tuple1)))
        self.assertTrue(is_matchobj(predicate3(self.tuple2)))

    def test_regex_returns_none_if_regex_doesnt_match(self):
        predicate = p.RegEx(self.test_re1)

        self.assertEquals(None, predicate(self.test_string2))
