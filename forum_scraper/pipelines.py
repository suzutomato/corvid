# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import csv
from collections import defaultdict
import json
import logging

from itemadapter import ItemAdapter

from corvid.utils.classes import ItemBuffer
from .items import (
    BaseForumItem,
    BaseTopicItem,
    BaseCommentItem,
    TopicCompletedItem
)
from .utils.fileutil import prepare_path
from .utils.pipelines import (
    remove_excess_spaces,
    to_iso8601
)


class DatetimePipeline:
    logger = logging.getLogger('pipelines.DatetimePipeline')

    def process_item(self, item, spider):
        # Process ForumItems
        if isinstance(item, BaseForumItem):
            pass

        # Process TopicItems
        elif isinstance(item, BaseTopicItem):
            to_iso8601(item, ['posted_on', 'last_comment_on'])

        # Process CommentItems
        elif isinstance(item, BaseCommentItem):
            to_iso8601(item, [('posted_on_raw', 'posted_on')])

        return item


class ForumItemExportPipeline:
    logger = logging.getLogger('pipelines.ForumItemExportPipeline')

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.logger.debug('initiated')

    @classmethod
    def from_crawler(cls, crawler):
        # Read params from settings
        kwargs = {
            'base_dir_path': crawler.settings.get('DATA_DIR'),
            'dirname_tmplt': crawler.settings.get('FORUM_DIR_TEMPLATE'),
            'filename_tmplt': crawler.settings.get('FORUM_METADATA_TEMPLATE')
        }
        return cls(**kwargs)

    def process_item(self, item, spider):
        # Only handle BaseForumItems
        if not isinstance(item, BaseForumItem):
            return item

        adapter = ItemAdapter(item)
        forum_id = adapter.get('forum_id')
        self.logger.debug(f'exporting ForumItem (id: {forum_id})')

        path = prepare_path(base_dir=self.base_dir_path,
                            dirname_template=self.dirname_tmplt,
                            filename_template=self.filename_tmplt,
                            item=item)
        with path.open('w') as wh:
            json.dump(adapter.asdict(), wh)

        self.logger.debug(f'exported ForumItem (id: {forum_id})')

        return item


class TopicItemExportPipeline:
    logger = logging.getLogger('pipelines.TopicItemExportPipeline')

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.logger.debug('initiated')

    @classmethod
    def from_crawler(cls, crawler):
        # Read params from settings
        kwargs = {
            'base_dir_path': crawler.settings.get('DATA_DIR'),
            'dirname_tmplt': crawler.settings.get('TOPIC_DIR_TEMPLATE'),
            'filename_tmplt': crawler.settings.get('TOPIC_METADATA_TEMPLATE')
        }
        return cls(**kwargs)

    def process_item(self, item, spider):
        # Only handle TopicItems
        if not isinstance(item, BaseTopicItem):
            return item

        adapter = ItemAdapter(item)
        topic_id = adapter.get('topic_id')
        self.logger.debug(f'exporting TopicItem (id: {topic_id})')

        path = prepare_path(base_dir=self.base_dir_path,
                            dirname_template=self.dirname_tmplt,
                            filename_template=self.filename_tmplt,
                            item=item)
        with path.open('w') as wh:
            json.dump(adapter.asdict(), wh)

        self.logger.debug(f'exported TopicItem (id: {topic_id})')

        return item


class CommentItemExportPipeline:
    logger = logging.getLogger('pipelines.CommentItemExportPipeline')

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.comment_item_buffers = defaultdict(ItemBuffer)
        self.logger.debug('initiated')

    @classmethod
    def from_crawler(cls, crawler):
        # Read params from settings
        kwargs = {
            'base_dir_path': crawler.settings.get('DATA_DIR'),
            'dirname_tmplt': crawler.settings.get('TOPIC_DIR_TEMPLATE'),
            'filename_tmplt': crawler.settings.get('TOPIC_CONTENTS_TEMPLATE')
        }
        return cls(**kwargs)

    def process_item(self, item, spider):
        # Only handle CommentItems
        if not isinstance(item, BaseCommentItem):
            return item

        adapter = ItemAdapter(item)
        topic_id = adapter.get('topic_id', 0)

        if isinstance(item, TopicCompletedItem):
            self.logger.debug(f'exporting CommentItems (id: {topic_id})')

            path = prepare_path(base_dir=self.base_dir_path,
                                dirname_template=self.dirname_tmplt,
                                filename_template=self.filename_tmplt,
                                item=dict(topic_id=topic_id))

            with path.open('w') as wh:
                writer = csv.writer(wh)
                for row in self.comment_item_buffers[topic_id]:
                    writer.writerow(row)

            self.logger.debug(f'exported CommentItems (id: {topic_id})')

        else:
            # Remove excess spaces if comment is not Ascii Art.
            if not adapter.get('is_aa') and not adapter.get('body'):
                adapter['is_aa'] = False
                remove_excess_spaces(item, 'body')

            self.comment_item_buffers[topic_id].store(item)

        return item
