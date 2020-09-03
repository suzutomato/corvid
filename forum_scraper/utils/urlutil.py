# -*- coding: utf-8 -*-
import json
import logging
import os
import re
from urllib.parse import urlparse

from corvid.utils.urlutil import get_sld_from_url

# Prepare logger
logger = logging.getLogger(__file__)

# Prepare domain dict with regex.
with open(os.environ['SITE_PARAMS_PATH']) as rh:
    SITE_PARAMS = json.load(rh)


def is_forum_url(url: str) -> bool:
    if not isinstance(url, str):
        raise TypeError()

    return parse_url(url, 'forum_pat')


def is_topic_url(url: str) -> bool:
    if not isinstance(url, str):
        raise TypeError()

    return parse_url(url, 'topic_pat')


def is_comment_url(url: str) -> bool:
    if not isinstance(url, str):
        raise TypeError

    # Is always a relative URL
    for site_info in SITE_PARAMS:
        m = re.match(site_info['comment_pat'], url)
        if m:
            return m

    return False


def parse_url(url: str, key: str):
    parsed = urlparse(url)

    for site_info in SITE_PARAMS:
        m = re.match(site_info[key], parsed.path)
        if site_info['domain'] in parsed.netloc and m:
            return m

    return None


def forum_id_from_url(url: str) -> str:

    m_frm = is_forum_url(url)
    m_tpc = is_topic_url(url)
    m_cmt = is_comment_url(url)

    if m_frm:
        m = m_frm
    elif m_tpc:
        m = m_tpc
    elif m_cmt:
        m = m_cmt
    else:
        return None

    sld = get_sld_from_url(url)
    return '_'.join([sld, m.group('forum_id')])


def topic_id_from_url(url: str) -> str:

    m_tpc = is_topic_url(url)
    m_cmt = is_comment_url(url)

    if m_tpc:
        m = m_tpc
    elif m_cmt:
        m = m_cmt
    else:
        return None

    sld = get_sld_from_url(url)
    return '_'.join([sld, m.group('forum_id'), m.group('topic_num')])


def comment_id_from_url(url: str) -> str:

    m = is_comment_url(url)

    if not m:
        return None

    sld = get_sld_from_url(url)
    return '_'.join([sld, m.group('forum_id'), m.group('topic_num'),
                     f'{int(m.group("comment_num")):0>4}'])


def extract_hostname(url: str) -> str:
    '''Extract hostname (hostloc, to be precise) from url. Used in loaders.

    Parametes
    ---------
    url : str
        URL to extract a host name (= netloc)from.

    Raises
    ------
    TypeError
        When `url` is not a `str`.

    Returns
    -------
    str
        a host name.

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
