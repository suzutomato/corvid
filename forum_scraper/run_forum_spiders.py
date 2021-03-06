# -*- coding: utf-8 -*-

import argparse
from copy import deepcopy
import os
from pathlib import Path
import sys

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def generate_settings(site, data_dir, site_params_path, start_time):

    latest_dir = data_dir / site / 'LATEST'
    if not latest_dir.exists():
        latest_dir.mkdir(parents=True)

    daily_dir = data_dir / site / start_time
    if not daily_dir.exists():
        daily_dir.mkdir()

    settings = deepcopy(get_project_settings())
    # Path of config files
    settings['SITE_PARAMS_PATH'] = site_params_path
    settings['LATEST_DIR_POINTER'] = str(latest_dir/'latest.txt')

    # Dir settings
    settings['IMAGES_STORE'] = str(data_dir/'images')
    settings['DAILY_DIR'] = str(daily_dir)
    settings['DATA_DIR'] = str(daily_dir/'data')

    # Templates
    settings['FORUM_DIR_TEMPLATE'] = '{forum_id}'
    settings['FORUM_METADATA_TEMPLATE'] = '{forum_id}_metadata.json'
    settings['TOPIC_DIR_TEMPLATE'] = '{forum_id}/{topic_id}'
    settings['TOPIC_METADATA_TEMPLATE'] = '{topic_id}_metadata.json'
    settings['TOPIC_CONTENTS_TEMPLATE'] = '{topic_id}_contents.csv'

    # Log levels
    settings['LOG_LEVEL'] = 'WARNING'
    settings['LOG_FILE'] = str(daily_dir/'log.txt')

    return settings


if __name__ == '__main__':
    src_path = str(Path(__file__).resolve().parents[1])
    sys.path.insert(0, src_path)

    # Config ArgumentParser
    parser = argparse.ArgumentParser(description='Parse Forums')
    parser.add_argument('-d', default='.', type=str, required=False,
                        dest='data_dir',
                        help='Base directory for files generated by spiders')
    parser.add_argument('-t', type=str, required=True, dest='start_time',
                        help='When the task is started, used for folder names')
    parser.add_argument('-s', type=str, required=True, dest='site',
                        help='Spider name')

    # Parse arguments
    args = parser.parse_args()
    data_dir = Path(args.data_dir)
    start_time = args.start_time
    site = args.site

    # Set BASE_DIR environment variable for utils.urlutil
    os.environ['SITE_PARAMS_PATH'] = site_params_path = \
        str(data_dir / 'corvid_config' / 'site_params.json')

    if site == '2ch':
        from forum_scraper.spiders.a2ch import A2chSpider
        spider = A2chSpider
    elif site == '5ch':
        from forum_scraper.spiders.a5ch import A5chSpider
        spider = A5chSpider
    else:
        raise ValueError(f'invalid site name {site}')

    # Retrieve the settings from `settings.py` file
    os.environ['SCRAPY_SETTINGS_MODULE'] = 'forum_scraper.settings'

    settings = generate_settings(site, data_dir, site_params_path, start_time)
    process = CrawlerProcess(settings)
    process.crawl(spider)
    process.start()
