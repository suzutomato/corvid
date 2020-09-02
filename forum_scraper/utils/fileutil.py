# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Any, Dict, Union

from itemadapter import ItemAdapter

from corvid.utils.fileutil import make_dirs


def get_parent_id(item_id: Union[str, None]) -> str:
    if item_id is None:
        return None

    if not isinstance(item_id, str):
        raise TypeError('not a str nor None')

    return item_id.rsplit('_', 1)[0]


def get_template_kwargs(item: Any) -> Dict[str, Any]:

    adapter = ItemAdapter(item)
    # Prepare Comment ID
    cmt_id = adapter.get('comment_id')
    # Prepare Topic ID
    tpc_id = adapter.get('topic_id')
    tpc_id = tpc_id if tpc_id else get_parent_id(cmt_id)

    frm_id = adapter.get('forum_id')
    frm_id = frm_id if frm_id else get_parent_id(tpc_id)

    kwargs = {'forum_id': frm_id, 'topic_id': tpc_id, 'comment_id': cmt_id}

    return kwargs


def prepare_path(base_dir: str, dirname_template: str, filename_template: str,
                 item: Any) -> str:

    template_kwags = get_template_kwargs(item)
    dir_path = make_dirs(base_dir, dirname_template, template_kwags)
    file_name = filename_template.format(**template_kwags)
    return Path(dir_path) / file_name
