# -*- coding: utf-8 -*-

import re
from typing import List, Union
from urllib.parse import urlparse, urlunparse

from w3lib import html

from .pipelines import DATETIME_PTTRN

_SPACE_CHARACTERS = '\t\n\x0b\x0c\r '


def extract_comment_counts(text: str) -> Union[str, None]:
    '''Extract comment counts from inner texts of '.pagestats .meta'.
    As the selector extracts 2 stats info (they are undistinguishable in terms
    of css selectors), filter it first.

    Example
    -------
    >>> text = '<li class="metastats meta centered">660コメント</li>'
    >>> extract_comment_counts(text)
    '660'
    '''
    if not isinstance(text, str):
        return None

    m = re.match(r'\d+ ?コメント', text)
    return None if m is None else re.match(r'\d+', text).group(0)


def extract_image_url(url: str) -> Union[str, None]:
    if not isinstance(url, str):
        return None

    url = urlparse(url)
    if (
        ('5ch.net' in url.netloc or '2ch.sc' in url.netloc)
        and url.query
    ):
        url = urlparse(url.query)

    if url.scheme == 'http' and url.netloc == 'i.imgur.com':
        url = url._replace(scheme='https')
    elif url.netloc == 'imgur.com':
        url = url._replace(scheme='https', netloc='i.imgur.com')

    return urlunparse(url)


def prep_comment_id(input):
    result = []
    for s in input:
        if len(s) <= 4 and s.isdigit():
            s = (f'{int(s):0>4}')
        result.append(s)
    return result


def filter_datetime(text: str) -> str:
    m = re.match(DATETIME_PTTRN, text)
    return text if m else None


def remove_span_img_tags(text: str) -> str:
    '''Remove <sapn> and <img> from body text.'''
    if not isinstance(text, str):
        return None

    return html.remove_tags(text, which_ones=('span', 'img'))


def strip_space_characters(text: str) -> str:
    '''Strip space charaters.

    Example
    -------
    >>> strip_space_characters('■■■ソ ー セ ー ジ18■■■       \n')
    '■■■ソ ー セ ー ジ18■■■'
    '''
    if not isinstance(text, str):
        return None

    return text.strip(_SPACE_CHARACTERS)


def take_last(array: List[Union[str, int, float]]) -> Union[str, int, float]:
    '''Return the last valid value from a list
    The same
    Example
    -------
    >>> take_last(['A', 'B", '', 'C', None, ''])
    'C'
    '''
    if not isinstance(array, list):
        return None

    for value in array[::-1]:
        if value is not None and value != '':
            return value

    return None


def to_byte_size(text: str) -> int:
    '''Extract data size from inner texts of '.pagestats .meta'.
    As the selector extracts 2 stats info (they are undistinguishable in terms
    of css selectors), filter it first. Then covert to B (1KB = 1024B).

    Example
    -------
    >>> to_byte_size('<li class="metastats meta centered">137KB</li>')
    '140288'
    '''
    if (
        not isinstance(text, str)
        or re.match(r'\d+ ?[KMGT]?B', text, flags=re.IGNORECASE) is None
    ):
        return None

    UNITS_MAPPING = {'B': 1, 'KB': 1 << 10, 'MB': 1 << 20, 'GB': 1 << 30}
    size = re.match(r'\d+', text).group(0)
    suffix = text[len(size):].strip().upper()
    factor = UNITS_MAPPING.get(suffix)
    return int(size) * factor


def to_int(text: str) -> Union[int, None]:
    '''Convert string to int if possible, otherwise return None.

    Example
    -------
    >>> to_int('182')
    182
    >>> to_int('192B')
    None
    '''
    if not isinstance(text, str) or not text.isdigit():
        return None

    return int(text)
