# -*- coding: utf-8 -*-

import pytest

from forum_scraper.utils import pipelines
from forum_scraper.tests.statics import VALID_DATETIME, PROCESSED_DATETIME


class TestFieldList:

    # ------------
    # Valid inputs
    # ------------
    @pytest.mark.parametrize('input,expected', [
        ('foo', [('foo', 'foo')]),  # hashable -> list of it (str)
        ([1.3], [(1.3, 1.3)]),  # hashable -> list of it (float)
        ((1, 2), [(1, 2)]),  # hashable -> list of it (tuple)
        ([('foo', 2)], [('foo', 2)]),  # list of tuples of hashables -> as is
        ([1.3, ('foo', 2)], [(1.3, 1.3), ('foo', 2)])  # combined case
    ])
    def test_fields_list(self, input, expected):
        actual = pipelines._fields_list(input)
        assert actual == expected

    # ------------
    # TypeErrors
    # ------------
    @pytest.mark.parametrize('input', [
        None,
        (None, 'foo'),  # Tuple contains None
        ([], 'foo'),  # Tuple contains non-hashable
        (1, {}),  # Tuple contains non-hashable
        [1, None],  # List contains None
        [[1]],  # Nested list
        [{}, 'foo'],  # dict in list
        [(None, 1), 'foo'],  # list contains tuple with None
        ['foo', (1.3, {})]  # list contains tuple with non-hashable
    ])
    def test_type_err(self, input):
        with pytest.raises(TypeError):
            pipelines._fields_list(input)

    # ------------
    # ValueErrors
    # ------------
    @pytest.mark.parametrize('input', [
        (1, 2, 3),  # tuple length is not 2
        (1,),  # tuple length is not 2
        []  # Empry list
    ])
    def test_value_err(self, input):
        with pytest.raises(ValueError):
            pipelines._fields_list(input)


class TestToIso8601:

    # ------------
    # Valid inputs
    # ------------
    @pytest.mark.parametrize('dt_str,expected', [
        (VALID_DATETIME, PROCESSED_DATETIME)
    ])
    def test_to_iso8601(self, dt_str, expected):
        item = {'time': dt_str}
        actual = pipelines.to_iso8601(item, 'time')
        assert actual is item
        assert actual['time'] == expected


class TestRemoveExcessSpaces:

    # ------------
    # Valid inputs
    # ------------
    @pytest.mark.parametrize('input,expected', [
        (None, None),
        ('', ''),
        (r' \n\x0cfoo bar<br><a>\r\t\x0b', 'foo bar<br><a>'),
        (r'foo      bar<br><a>', 'foo bar<br><a>'),
        (r'foo bar <br> <a>', 'foo bar<br><a>'),
        (r'foo bar<br><a >', 'foo bar<br><a>')
    ])
    def test_valid_body(self, input, expected):
        item = {'body': input}
        actual = pipelines.remove_excess_spaces(item, 'body')
        assert actual is item
        assert actual['body'] == expected
