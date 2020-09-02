# -*- conding: utf-8 -*-
from copy import deepcopy
from pathlib import Path
import pytest
from unittest.mock import Mock

from scrapy.exceptions import IgnoreRequest

from forum_scraper.items import (
    BaseForumItem,
    BaseCommentItem,
    ArchivedTopicItem
)
from forum_scraper.middlewares import DownloaderMiddleware
from forum_scraper.utils.exceptions import (
    BlacklistedURLException,
    ExpiredURLException,
    AlreadyScrapedURLsException
)


@pytest.fixture
def mock_mw():
    tests_dir = Path(__file__).parents[0] / 'data'
    fake_date = '2020_0101'
    last_dir_name = tests_dir / 'LATEST' / 'latest.txt'
    daily_dir_name = tests_dir / fake_date
    with open(last_dir_name, 'w') as wh:
        wh.write(str(daily_dir_name))

    return DownloaderMiddleware(last_dir_name, daily_dir_name)


class MockRequest:
    def __init__(self, url):
        self.url = url


class MockResponse:
    def __init__(self, status, url=None):
        self.status = status
        self.url = url


class TestDownloaderMiddlewareProcRequese:
    @pytest.mark.parametrize('url', [
        'https://mao.5ch.net/test/read.cgi/bass/1579966729/',
        'https://mao.5ch.net/test/read.cgi/bass/1579967891/',
        'https://mao.5ch.net/test/read.cgi/bass/1579964567'
    ])
    def test_valid_urls(self, url, mock_mw):
        request = MockRequest(url)
        assert mock_mw.process_request(request, Mock()) is None

    @pytest.mark.parametrize('url', [
        'https://agree.5ch.net/mango',
        'https://qb5.5ch.net/saku2ch',
        'https://mao.5ch.net/accuse',
        'https://headline.5ch.net/bbypinkH0/',
        'https://headline.5ch.net/bbypinkH1/'
    ])
    def test_blacklist(self, url, mock_mw):
        request = MockRequest(url)
        try:
            mock_mw.process_request(request, Mock())
        except BlacklistedURLException as e:
            assert isinstance(e, IgnoreRequest)

    @pytest.mark.parametrize('url', [
        'https://mao.5ch.net/test/read.cgi/bass/1579960729/',
        'https://egg.5ch.net/test/read.cgi/ruins/1491723120/'
    ])
    def test_expired(self, url, mock_mw):
        request = MockRequest(url)
        try:
            mock_mw.process_request(request, Mock())
        except ExpiredURLException as e:
            assert isinstance(e, IgnoreRequest)

    @pytest.mark.parametrize('url', [
        'https://mao.5ch.net/test/read.cgi/bass/1579960720/',
        'https://mao.5ch.net/test/read.cgi/bass/1579960721/',
        'https://mao.5ch.net/test/read.cgi/bass/1579960722/'
    ])
    def test_scraped(self, url, mock_mw):
        request = MockRequest(url)
        try:
            mock_mw.process_request(request, Mock())
        except AlreadyScrapedURLsException as e:
            assert isinstance(e, IgnoreRequest)


class TestDownloaderMiddlewareProcResponse:

    @pytest.mark.parametrize('url,status', [
        ('http://host.5ch.net/foo_good', 200),
        ('http://host.5ch.net/bar_good/', 200),
        ('http://host.5ch.net/test/read.cgi/foo/122131313', 200)
    ])
    def test_valid_response(self, url, status, mock_mw):
        request = MockRequest(url)
        response = MockResponse(status)
        actual = mock_mw.process_response(request, response, Mock())
        assert actual is response

    @pytest.mark.parametrize('url,status', [
        ('http://host.5ch.net/foo_banned', 400),
        ('http://host.5ch.net/bar_banned/', 403),
        ('http://host.5ch.net/foobar_banned/', 410)
    ])
    def test_blacklist(self, url, status, mock_mw):
        request = MockRequest(url)
        response = MockResponse(status)
        try:
            mock_mw.process_response(request, response, Mock())
        except BlacklistedURLException as e:
            url in mock_mw.blacklist
            assert isinstance(e, IgnoreRequest)

    @pytest.mark.parametrize('url,status,forum_id', [
        ('http://host.5ch.net/test/read.cgi/foo/45678900', 400, 'foo'),
        ('http://host.5ch.net/test/read.cgi/bar/56789121/', 403, 'bar'),
        ('http://host.5ch.net/test/read.cgi/foobar/12122124/', 410, 'foobar')
    ])
    def test_expired(self, url, status, forum_id, mock_mw):
        request = MockRequest(url)
        response = MockResponse(status)
        try:
            mock_mw.process_response(request, response, Mock())
        except ExpiredURLException as e:
            url == mock_mw.expired_urls[forum_id][0]
            assert isinstance(e, IgnoreRequest)


class FakeForumItem(BaseForumItem):
    pass


class FakeCommentItem(BaseCommentItem):
    pass


class TestDownloaderMiddlewareItemScraped:

    @pytest.mark.parametrize('url,topic_id', [
        ('https://host.5ch.net/test/read.cgi/thditem/45678900', 'thditem')
    ])
    def test_topic_item(self, url, topic_id, mock_mw):
        response = MockResponse(200, url)
        item = ArchivedTopicItem(topic_id=topic_id)
        len_before = len(mock_mw.scraped_urls.get(topic_id, []))

        mock_mw.item_scraped(item, response, Mock())
        assert mock_mw.scraped_urls.get(topic_id) is not None
        assert len(mock_mw.scraped_urls[topic_id]) == len_before + 1
        assert mock_mw.scraped_urls[topic_id][0] == url

    def test_another_item_type(self, mock_mw):
        scraped_urls_before = deepcopy(mock_mw.scraped_urls)
        response = spider = Mock()

        item = FakeCommentItem()
        mock_mw.item_scraped(item, response, spider)
        assert mock_mw.scraped_urls == scraped_urls_before

        item = FakeForumItem()
        mock_mw.item_scraped(item, response, spider)
        assert mock_mw.scraped_urls == scraped_urls_before


class TestDownloaderMiddlewareSpiderClosed:

    def test_is_trimed(self, mock_mw, mocker):
        to_pickle = mocker.patch('forum_scraper.middlewares.to_pickle')

        for i in range(1100):
            fake_url = f'http://host.5ch.net/test/read.cgi/fake/{i:0>6}/'
            mock_mw.scraped_urls['fake'].add_url(fake_url)
            mock_mw.expired_urls['fake'].add_url(fake_url)

        scrpd_urls = mock_mw.scraped_urls['fake']
        exprd_urls = mock_mw.expired_urls['fake']
        mock_mw.spider_closed(Mock(), 'for test')
        assert len(scrpd_urls) == 1000
        assert scrpd_urls.pivot_url == scrpd_urls[0]
        assert len(exprd_urls) == 1000
        assert exprd_urls.pivot_url == exprd_urls[0]

        to_pickle.assert_any_call(mock_mw.blacklist,
                                  mock_mw.daily_dir/'blacklist.pickle')
        to_pickle.assert_any_call(mock_mw.scraped_urls,
                                  mock_mw.daily_dir/'scraped_urls.pickle')
        to_pickle.assert_any_call(mock_mw.expired_urls,
                                  mock_mw.daily_dir/'expired_urls.pickle')
        assert to_pickle.call_count == 3
