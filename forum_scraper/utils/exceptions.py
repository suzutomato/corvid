from scrapy.exceptions import IgnoreRequest


class BlacklistedURLException(IgnoreRequest):
    pass


class ExpiredURLException(IgnoreRequest):
    pass


class AlreadyScrapedURLsException(IgnoreRequest):
    pass
