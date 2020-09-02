from urllib.parse import urlparse


def get_sld_from_url(url: str):
    if not isinstance(url, str):
        sld = None

    parsed = urlparse(url)
    sld = parsed.netloc.split('.')[-2]

    return sld
