# -*- coding: utf-8 -*-
import pytest

from forum_scraper.utils import urlutil

TEST_URLS = [
    # 2 x Forum URLs
    'https://hayabusa9.5ch.net/mnewsplus/',
    'http://hayabusa5.2ch.sc/mnewsplus',
    # 5 x Topic URL
    'https://hayabusa9.5ch.net/test/read.cgi/mnewsplus/1597213268/',
    'http://hayabusa9.5ch.net/test/read.cgi/mnewsplus/1597213268',
    'http://hayabusa5.2ch.sc/test/read.cgi/mnewsplus/1597213268/l50',
    'http://hayabusa5.2ch.sc/test/read.cgi/mnewsplus/1597213268/-100',
    'http://hayabusa5.2ch.sc/mnewsplus/dat/1597213268.dat',
    # 3 x Comment URL
    '../test/read.cgi/mnewsplus/1597213268/72',  # Relative Comment URL A
    '/test/read.cgi/mnewsplus/1597213268/72'  # Relative Comment URL B
]


class TestForumIdFromUrl:
    @pytest.mark.parametrize('input,expected', [
        *zip(TEST_URLS, ['mnewsplus']*9)
    ])
    def test_valid_input(self, input, expected):
        actual = urlutil.forum_id_from_url(input)
        assert actual == expected


class TestTopicIdFromUrl:
    @pytest.mark.parametrize('input,expected', [
        *zip(TEST_URLS, [None]*2+['mnewsplus_1597213268']*7)
    ])
    def test_valid_input(self, input, expected):
        actual = urlutil.topic_id_from_url(input)
        assert actual == expected


class TestCommentIdFromUrl:
    @pytest.mark.parametrize('input,expected', [
        *zip(TEST_URLS, [None]*7+['mnewsplus_1597213268_0072']*2)
    ])
    def test_valid_input(self, input, expected):
        actual = urlutil.comment_id_from_url(input)
        assert actual == expected


class TestIsForumUrl:
    @pytest.mark.parametrize('input,expected', [
        *zip(TEST_URLS, [True]*2+[False]*7)
    ])
    def test_valid_input(self, input, expected):
        actual = urlutil.is_forum_url(input)
        assert actual == expected


class TestIsTopicUrl:
    @pytest.mark.parametrize('input,expected', [
        *zip(TEST_URLS, [False]*2+[True]*5+[False]*2)
    ])
    def test_valid_input(self, input, expected):
        actual = urlutil.is_topic_url(input)
        assert actual == expected


class TestIsCommentUrl:
    @pytest.mark.parametrize('input,expected', [
        *zip(TEST_URLS, [False]*7+[True]*2)
    ])
    def test_valid_input(self, input, expected):
        actual = urlutil.is_comment_url(input)
        assert actual == expected


class TestExtractHostname:
    @pytest.mark.parametrize('input,expected', [
        *zip(TEST_URLS,
             ['hayabusa9.5ch.net', 'hayabusa5.2ch.sc', 'hayabusa9.5ch.net',
              'hayabusa9.5ch.net', 'hayabusa5.2ch.sc', 'hayabusa5.2ch.sc',
              'hayabusa5.2ch.sc', None, None])
    ])
    def test_valid_input(self, input, expected):
        actual = urlutil.extract_hostname(input)
        assert actual == expected
