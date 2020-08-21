# -*- coding: utf-8 -*-

# Define loaders for scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/loaders.html

from scrapy.loader import ItemLoader
from scrapy.loader.processors import (
    Compose,
    MapCompose,
    Identity,
    Join,
    TakeFirst
)

from .utils.loaders import (
    extract_comment_counts,
    extract_image_url,
    filter_datetime,
    prep_comment_id,
    remove_span_img_tags,
    strip_space_characters,
    take_last,
    to_int,
    to_byte_size
)
from .utils.urlutil import (
    forum_id_from_url,
    topic_id_from_url,
    comment_id_from_url,
    extract_hostname
)


class ForumLoader(ItemLoader):
    '''Item loader for ForumItem.'''
    # Default processors
    default_input_processor = Identity()
    default_output_processor = TakeFirst()

    # Custom input processors
    forum_id_in = MapCompose(forum_id_from_url)
    hostname_in = MapCompose(extract_hostname)


class TopicLoader(ItemLoader):
    '''Item loader for TopicItem.'''
    # Default processors
    default_input_processor = Identity()
    default_output_processor = TakeFirst()

    # Custom input processors
    topic_id_in = MapCompose(topic_id_from_url)
    topic_title_in = MapCompose(strip_space_characters)
    num_comments_in = MapCompose(extract_comment_counts, to_int)
    reported_size_in = MapCompose(to_byte_size)
    last_comment_on_out = MapCompose(filter_datetime)

    # Custom output processors
    last_comment_on_out = take_last


class CommentLoader(ItemLoader):
    '''Item loader for CommentItem.'''
    # Default processors
    default_input_processor = Identity()
    default_output_processor = TakeFirst()

    # Custom input processors
    # Basic identity
    comment_id_in = prep_comment_id
    # Metadata
    user_name = MapCompose(strip_space_characters)
    reply_to_in = MapCompose(comment_id_from_url)
    image_urls_in = MapCompose(extract_image_url)

    # Custom output processors
    # Metadata
    comment_id_out = Join('_')
    comment_url_out = Join('/')
    body_out = Compose(Join(), strip_space_characters, remove_span_img_tags)
    reply_to_out = Identity()  # To keep as a list
    is_aa_out = Compose(TakeFirst(), bool)
    image_urls_out = Identity()  # To keep as a list
