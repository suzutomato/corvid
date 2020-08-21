# -*- encoding: utf-8 -*-

import pytest

from forum_scraper.utils import loaders


class TestExtractCommentCounts:
    # ------------
    # Valid inputs
    # ------------
    @pytest.mark.parametrize('input,expected', [
        (None, None),
        ('', None),  # Not counts -> None
        ('3KB', None),  # Not comment counts -> None
        ('123', None),  # Not comment counts -> None
        ('11コメント', '11'),  # comment counts -> digits (str)
        ('11 コメント', '11')  # comment counts -> digits (str)
    ])
    def test_extract_comment_count(self, input, expected):
        actual = loaders.extract_comment_counts(input)
        assert actual == expected


class TestRemoveSpanImgTags:
    # ------------
    # Valid inputs
    # ------------
    @pytest.mark.parametrize('input,expected', [
        (None, None),  # None -> None
        ([], None),  # Not str -> None
        ({}, None),  # Not str -> None
        (1, None),  # Not str -> None
        ('<span><img></span>', ''),  # Only tags to remove -> empty string
        ('<span<img', '<span<img'),  # Incomplete tags -> as is
        ('<span>', ''),  # Should remove unclosed tag
        ('<span><img><br><a></a></span>', '<br><a></a>')  # Valid string
    ])
    def test_remove_span_img_tags(self, input, expected):
        actual = loaders.remove_span_img_tags(input)
        assert actual == expected


class TestStripSpaceCharacters:
    # ------------
    # Valid inputs
    # ------------
    @pytest.mark.parametrize('input,expected', [
        (None, None),  # None -> None
        (1, None),  # Not str -> None
        ([], None),  # Not str -> None
        ('  ', ''),  # Only space chars -> empty string
        ('\t\n\x0b\x0c\r test       \n', 'test'),  # Valid -> strip
        ('t n x0b x0c r n', 't n x0b x0c r n')  # just to be sure
    ])
    def test_strip_space_charcters(self, input, expected):
        actual = loaders.strip_space_characters(input)
        assert actual == expected


class TestTakeLast:
    # ------------
    # Valid inputs
    # ------------
    @pytest.mark.parametrize('input,expected', [
        (None, None),  # None -> None
        (1, None),  # Not a list -> None
        ([], None),  # Empty list -> None
        ([None, ''], None),  # All element None or empty string -> None
        (['first', 'second', 'last'], 'last'),
        (['first', 'second', ''], 'second'),
        (['first', None, ''], 'first'),
    ])
    def test_take_last(self, input, expected):
        actual = loaders.take_last(input)
        assert actual == expected


class TestToByteSize:
    # ------------
    # Valid inputs
    # ------------
    @pytest.mark.parametrize('input,expected', [
        (None, None),  # None -> None
        ([], None),  # Not str -> None
        (1, None),  # Not str -> None
        ('11 コメント', None),  # Invalid str -> None
        ('1B', 1),  # Valid str (B) -> 1
        ('1KB', 1024),  # Valid str (KB) -> 2 << 10
        ('1MB', 1048576),  # Valid str (MB) -> 2 << 20
        ('1GB', 1073741824)  # Valid str (GB) -> 2 << 30
    ])
    def test_to_byte_size(self, input, expected):
        actual = loaders.to_byte_size(input)
        assert actual == expected


class TestToInt:
    @pytest.mark.parametrize('input,expected', [
        (None, None),
        (1, None),
        ([], None),
        ('1', 1),
        ('1.4', None)
    ])
    def test_to_int(self, input, expected):
        actual = loaders.to_int(input)
        assert actual == expected
