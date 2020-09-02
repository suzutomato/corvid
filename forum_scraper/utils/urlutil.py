# -*- coding: utf-8 -*-
import re
from urllib.parse import urlparse

FORUM_PATTERN = r'^https?://\w+\.(?:5ch\.net|2ch\.sc)/\w+/?$'

TOPIC_PATTERN_2CH = r'^/(?:test/read\.cgi/)?(?P<forum_id>\w+)/' + \
                        r'(?:dat/)?(?P<topic_num>\d+)(?:\.dat)?/?(?:\D\d+)?$'
TOPIC_PATTERN_5CH = r'^/test/read\.cgi/(?P<forum_id>\w+)/' + \
                     r'(?P<topic_num>\d+)/?(?:\D\d+)?$'

COMMENT_PATTERN = r'(?:\.\.)?/test/read\.cgi/(?P<forum_id>\w+)/' + \
                  r'(?P<topic_num>\d+)/(?P<comment_num>\d+)/?'

DOMAIN_2CH = '2ch.sc'
DOMAIN_5CH = '5ch.net'


def forum_id_from_url(url: str) -> str:
    if is_forum_url(url):
        return urlparse(url).path.strip('/')
    elif is_topic_url(url):
        parsed = urlparse(url)
        if DOMAIN_2CH in parsed.netloc:
            m = re.match(TOPIC_PATTERN_2CH, parsed.path)
        if DOMAIN_5CH in parsed.netloc:
            m = re.match(TOPIC_PATTERN_5CH, parsed.path)
        return m.group('forum_id')
    elif is_comment_url(url):
        return re.match(COMMENT_PATTERN, url).group('forum_id')

    return None


def topic_id_from_url(url: str) -> str:
    if is_topic_url(url):
        parsed = urlparse(url)
        if DOMAIN_2CH in parsed.netloc:
            m = re.search(TOPIC_PATTERN_2CH, parsed.path)
        if DOMAIN_5CH in parsed.netloc:
            m = re.search(TOPIC_PATTERN_5CH, parsed.path)
    elif is_comment_url(url):
        m = re.search(COMMENT_PATTERN, url)
    else:
        return None

    return '_'.join([m.group('forum_id'), m.group('topic_num')])


def comment_id_from_url(url: str) -> str:
    if is_comment_url(url):
        m = re.search(COMMENT_PATTERN, url)
        comment_num = f'{int(m.group("comment_num")):0>4}'
        return '_'.join([m.group('forum_id'), m.group('topic_num'),
                        comment_num])
    else:
        return None


def is_forum_url(url: str) -> bool:
    if not isinstance(url, str):
        raise TypeError()

    return re.match(FORUM_PATTERN, url) is not None


def is_topic_url(url: str) -> bool:
    if not isinstance(url, str):
        raise TypeError()

    parsed = urlparse(url)
    if DOMAIN_2CH in parsed.netloc:
        return re.match(TOPIC_PATTERN_2CH, parsed.path) is not None
    if DOMAIN_5CH in parsed.netloc:
        return re.match(TOPIC_PATTERN_5CH, parsed.path) is not None
    return False


def is_comment_url(url: str) -> bool:
    if not isinstance(url, str):
        raise TypeError
    return re.match(COMMENT_PATTERN, url) is not None


def extract_hostname(url: str) -> str:
    '''Extract hostname (hostloc, to be precise) from url.

    Example
    -------
    >>> extract_hostname('https://matsuri.5ch.net/nissin')
    'matsuri.5ch.net'
    '''
    if not isinstance(url, str):
        raise TypeError()

    if url.startswith('http'):
        return urlparse(url).netloc
    else:
        return None
