"""Retainn web-fetching functions."""

try:
    # Python 3
    from urllib.request import Request, urlopen
except ImportError:
    # Python 2
    from urllib2 import Request, urlopen


def http_get_deck_and_etag(gist_url):
    """Download the markdown and etag of a deck URL."""
    response = urlopen(gist_url + "/raw")
    markdown = response.read()
    etag = response.headers['etag']
    return (markdown, etag)


def http_head_deck_etag(gist_url):
    """Perform a HEAD against gist_url and return the etag."""    
    class HeadRequest(Request):
        def get_method(self):
            return 'HEAD'
    head_request = HeadRequest(gist_url + '/raw')
    response = urlopen(head_request)
    headers = response.headers
    etag = headers['etag']
    return etag


def http_get_deck_if_needed(gist_url, previous_etag):
    """Fetch deck markdown + etag if etag is out of date."""
    current_etag = http_head_deck_etag(gist_url)
    if current_etag == previous_etag:
        return (None, None)
    else:
        (markdown, current_etag) = http_get_deck_and_etag(gist_url)
        return (markdown, current_etag)
