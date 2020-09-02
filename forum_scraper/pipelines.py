# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import csv
from collections import defaultdict
import json

from itemadapter import ItemAdapter
import logging

from .utils.fileutil import prepare_path
from .items import (
    BaseForumItem,
    BaseTopicItem,
    BaseCommentItem,
    TopicCompletedItem
)
from .utils.pipelines import (
    remove_excess_spaces,
    to_iso8601
)


class DatetimePipeline:
    logger = logging.getLogger('utils.pipelines.DatetimePipeline')

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
    logger = logging.getLogger('utils.pipelines.ForumItemExportPipeline')

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.logger.debug('initiated')

    @classmethod
    def from_crawler(cls, crawler):
        kwargs = {
            'base_dir_path': crawler.settings.get('DATA_DIR'),
            'dirname_tmplt': crawler.settings.get('FORUM_DIR_TEMPLATE'),
            'filename_tmplt': crawler.settings.get('FORUM_METADATA_TEMPLATE')
        }
        return cls(**kwargs)

    def process_item(self, item, spider):
        if not isinstance(item, BaseForumItem):
            return item

        adapter = ItemAdapter(item)
        start_msg = f'exporting ForumItem (id: {adapter.get("forum_id")})'
        self.logger.debug(start_msg)
        path = prepare_path(base_dir=self.base_dir_path,
                            dirname_template=self.dirname_tmplt,
                            filename_template=self.filename_tmplt,
                            item=item)
        with open(path, 'w', encoding='utf-8') as wh:
            json.dump(adapter.asdict(), wh)
        finish_msg = f'exporting ForumItem (id: {adapter.get("forum_id")})'
        self.logger.debug(finish_msg)
        return item


class TopicItemExportPipeline:
    logger = logging.getLogger('utils.pipelines.TopicItemExportPipeline')

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def from_crawler(cls, crawler):
        kwargs = {
            'base_dir_path': crawler.settings.get('DATA_DIR'),
            'dirname_tmplt': crawler.settings.get('TOPIC_DIR_TEMPLATE'),
            'filename_tmplt': crawler.settings.get('TOPIC_METADATA_TEMPLATE')
        }
        return cls(**kwargs)

    def process_item(self, item, spider):
        if not isinstance(item, BaseTopicItem):
            return item

        path = prepare_path(base_dir=self.base_dir_path,
                            dirname_template=self.dirname_tmplt,
                            filename_template=self.filename_tmplt,
                            item=item)

        adapter = ItemAdapter(item)
        with open(path, 'w', encoding='utf-8') as wh:
            json.dump(adapter.asdict(), wh)

        return item


class CommentItemExportPipeline:
    logger = logging.getLogger('utils.pipelines.CommentItemExportPipeline')

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def from_crawler(cls, crawler):
        kwargs = {
            'base_dir_path': crawler.settings.get('DATA_DIR'),
            'dirname_tmplt': crawler.settings.get('TOPIC_DIR_TEMPLATE'),
            'filename_tmplt': crawler.settings.get('TOPIC_CONTENTS_TEMPLATE')
        }

        return cls(**kwargs)

    def open_spider(self, spider):
        # Build a topic
        '''
        self.comment_item_exporters = \
            CommentItemExporterDict(data_dir_path=self.base_dir_path,
                                    thd_dir_tmplt=self.dirname_tmplt,
                                    thd_cont_tmplt=self.filename_tmplt,
                                    exporter=CsvItemExporter,
                                    encoding='utf-8',
                                    delimiter='\t')
        '''
        self.comment_item_buffers = defaultdict(CommentItemBuffer)
        self.logger.debug('CommentItemExporterDict created')

    def process_item(self, item, spider):
        if not isinstance(item, BaseCommentItem):
            return item

        # Remove excess spaces if comment is not Ascii Art.
        adapter = ItemAdapter(item)
        if not adapter.get('is_aa') and not adapter.get('body'):
            adapter['is_aa'] = False
            remove_excess_spaces(item, 'body')

        # Export item through Content Exporter
        topic_id = adapter.get('topic_id', 0)

        if isinstance(item, TopicCompletedItem):
            path = prepare_path(base_dir=self.base_dir_path,
                                dirname_template=self.dirname_tmplt,
                                filename_template=self.filename_tmplt,
                                item=dict(topic_id=topic_id))
            with open(path, 'w') as wh:
                writer = csv.writer(wh, delimiter='\t')
                for row in self.comment_item_buffers[topic_id]:
                    writer.writerow(row)

            '''
            self.comment_item_exporters[topic_id].finish_exporting()
            '''
            self.logger.debug(f'{topic_id} completed')
        else:
            self.comment_item_buffers[topic_id].store(item)
            # self.comment_item_exporters[topic_id].export_item(item)

        return item


class CommentItemBuffer:
    def __init__(self):
        self._headers_not_written = True
        self.buffer = []
        self.header = []

    def __iter__(self):
        for row in self.buffer:
            yield row

    def store(self, item):
        adapter = ItemAdapter(item)
        if self._headers_not_written:
            self.header = adapter.field_names()
            self.buffer.append(self.header)
            self._headers_not_written = False

        temp = []
        for field in self.header:
            val = adapter.get(field)
            if isinstance(val, list):
                val = ','.join([str(v) for v in val])
            temp.append(val)
        self.buffer.append(temp)
