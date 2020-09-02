# -*- coding: utf-8 -*-

from collections.abc import Hashable
from datetime import datetime
import re
from typing import Any, List, Tuple, Union

from itemadapter import ItemAdapter

# Type hints
LIST_OF_TUPLES = List[Tuple[Hashable, Any]]
FIELDS = Union[Hashable, List[Union[Hashable, Tuple[Hashable, Any]]]]

# Regex pattern to extract datetime from comments
DATETIME_PTTRN = \
    r'(?P<date>\d{2,4}/\d{2}/\d{2})\D+(?P<time>\d{2}:\d{2}(:\d{2})?)'


def _fields_list(fields: FIELDS, is_child=False) -> List[Tuple[Hashable, Any]]:

    if isinstance(fields, tuple):
        if len(fields) != 2:
            raise ValueError(f'fields tuple longer than 2: {fields}')
        if any([not isinstance(f, Hashable) or f is None for f in fields]):
            raise TypeError(f'field name not hashable: {fields}')
        return [fields]

    elif fields is not None and isinstance(fields, Hashable):
        return [(fields, fields)]

    elif isinstance(fields, dict):
        if is_child:
            raise TypeError('fields shouldn\'t be a list of dicts')
        return _fields_list(list(fields.keys()))

    elif isinstance(fields, list):
        if is_child:
            raise TypeError('fields shouldn\'t be a nested list')
        if not fields:
            raise ValueError(f'empty list: {fields}')
        return sum([_fields_list(e, True) for e in fields], [])

    else:
        msg = f"Expected a hashable, tuple, or list (provided {type(fields)})"
        raise TypeError(msg)


def _get_item_id(item: Any) -> str:

    adapter = item if isinstance(item, ItemAdapter) else ItemAdapter(item)
    item_id = adapter.get('comment_id')
    item_id = adapter.get('topic_id') if item_id is None else item_id
    item_id = adapter.get('forum_id') if item_id is None else item_id
    return item_id


def to_iso8601(item: Any, fields: FIELDS) -> Any:
    '''Format a date string into ISO format.

    Example
    -------
    >>> to_timestr('2019/04/12(金) 19:12:51.87')
    '2019-04-12T19:12:51+09:00'
    '''

    adapter = item if isinstance(item, ItemAdapter) else ItemAdapter(item)
    fields = _fields_list(fields)

    for src, dest in fields:
        text = adapter.get(src)
        if isinstance(text, str):
            m = re.search(DATETIME_PTTRN, text)
            if m is not None:
                date = m.group('date')
                time = m.group('time')

                frmt = '%Y/%m/%d%H:%M:%S'
                if len(date) == 8:
                    frmt = frmt.replace('%Y', '%y')
                if len(time) == 5:
                    frmt = frmt.replace(':%S', '')

                dt = datetime.strptime(date+time, frmt)
                adapter[dest] = dt.strftime('%Y-%m-%dT%H:%M:%S+09:00')
            else:
                adapter[dest] = None

    return item


def remove_excess_spaces(item: Any, fields: FIELDS) -> Any:

    adapter = item if isinstance(item, ItemAdapter) else ItemAdapter(item)
    fields = _fields_list(fields)
    ESCAPE_CHARACTERS = r'\t\n\x0b\x0c\r '

    for src, dest in fields:
        text = adapter.get(src)
        if isinstance(text, str):
            text = text.strip(ESCAPE_CHARACTERS)
            text = re.sub(r'['+ESCAPE_CHARACTERS+r']+', ' ', text)
            text = text.replace(' <br>', '<br>').replace('<br> ', '<br>')
            text = text.replace(' >', '>')
            adapter[dest] = text

    return item
