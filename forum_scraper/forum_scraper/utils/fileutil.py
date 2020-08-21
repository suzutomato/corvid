# -*- encoding: utf-8 -*-

import os
from pathlib import Path
import pickle
from typing import Any, Dict, Union

from itemadapter import ItemAdapter


def get_parent_id(item_id: Union[str, None]) -> str:
    if item_id is None:
        return None

    if not isinstance(item_id, str):
        raise TypeError('not a str nor None')

    return item_id.rsplit('_', 1)[0]


def get_template_kwargs(item: Any) -> Dict[str, Any]:

    adapter = ItemAdapter(item)
    cmt_id = adapter.get('comment_id')
    thd_id = adapter.get('topic_id') if adapter.get('topic_id') \
        else get_parent_id(cmt_id)
    brd_id = adapter.get('forum_id') if adapter.get('forum_id') \
        else get_parent_id(thd_id)

    template_kwargs = {'forum_id': brd_id, 'topic_id': thd_id,
                       'comment_id': cmt_id}

    return template_kwargs


def make_dirs(base_dir: str,
              dirname_template: str,
              template_kwags: str) -> str:

    dirname = dirname_template.format(**template_kwags)
    path = os.path.join(base_dir, dirname)
    if not os.path.exists(path):
        os.makedirs(path)

    return path


def prepare_path(base_dir: str, dirname_template: str, filename_template: str,
                 item: Any) -> str:

    template_kwags = get_template_kwargs(item)
    dir_path = make_dirs(base_dir, dirname_template, template_kwags)
    file_name = filename_template.format(**template_kwags)
    return os.path.join(dir_path, file_name)


def read_pickle(path, default):
    if os.path.exists(path):
        with open(path, 'rb') as rh:
            return pickle.load(rh)
    else:
        return default


def to_pickle(obj, path):
    path = Path(path)
    parent = path.parents[0]
    if not os.path.exists(parent):
        os.makedirs(parent)
    with open(path, 'wb') as wh:
        pickle.dump(obj, wh)
