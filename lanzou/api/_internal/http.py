import re
from urllib.parse import urljoin, urlparse, urlunparse

import requests

from lanzou.api.utils import calc_acw_sc__v2, logger

LANZOU_SHARE_DOMAINS = (
    "lanzouw.com",
    "lanzoui.com",
    "lanzoux.com",
    "lanzouo.com",
)

_LANZOU_HOST_RE = re.compile(r"lanzou[a-z]\.com$", re.I)


def expand_lanzou_urls(url):
    """Expand lanzou share domains while preserving subdomains and paths."""
    parsed = urlparse(url)
    if not _LANZOU_HOST_RE.search(parsed.netloc):
        return [url]

    match = _LANZOU_HOST_RE.search(parsed.netloc)
    prefix = parsed.netloc[:match.start()]
    current_domain = parsed.netloc[match.start():]

    urls = []
    for domain in (current_domain,) + tuple(d for d in LANZOU_SHARE_DOMAINS if d != current_domain):
        candidate = parsed._replace(netloc=prefix + domain)
        candidate_url = urlunparse(candidate)
        if candidate_url not in urls:
            urls.append(candidate_url)
    return urls


def share_origin(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def join_share_url(base_url, path):
    return urljoin(base_url, path)


def build_browser_headers(base_headers, referer=None, origin=None, extra=None):
    headers = dict(base_headers)
    if referer is not None:
        headers["Referer"] = referer
    if origin is not None:
        headers["Origin"] = origin
    if extra:
        headers.update(extra)
    return headers


class LanZouHTTPClient(object):
    def __init__(self, session, headers, timeout=15):
        self.session = session
        self.headers = headers
        self.timeout = timeout

    @staticmethod
    def _should_retry_with_acw(response):
        content_type = response.headers.get("content-type", "")
        if "html" not in content_type and "text" not in content_type:
            return False
        text = response.text
        return "acw_sc__v2" in text or "arg1='" in text

    def request(self, method, url, data=None, **kwargs):
        allow_acw_retry = kwargs.pop("allow_acw_retry", False)
        timeout = kwargs.pop("timeout", self.timeout)
        custom_headers = kwargs.pop("headers", None)
        headers = dict(self.headers)
        if custom_headers:
            headers.update(custom_headers)

        for possible_url in expand_lanzou_urls(url):
            try:
                response = self.session.request(
                    method,
                    possible_url,
                    data=data,
                    headers=headers,
                    timeout=timeout,
                    verify=False,
                    **kwargs,
                )
                if allow_acw_retry and self._should_retry_with_acw(response):
                    acw_sc__v2 = calc_acw_sc__v2(response.text)
                    self.session.cookies.set("acw_sc__v2", acw_sc__v2)
                    logger.debug(f"Set Cookie: acw_sc__v2={acw_sc__v2}")
                    response = self.session.request(
                        method,
                        possible_url,
                        data=data,
                        headers=headers,
                        timeout=timeout,
                        verify=False,
                        **kwargs,
                    )
                return response
            except requests.RequestException:
                logger.debug(f"{method.upper()} {possible_url} failed, try another domain")
        return None

    def get(self, url, **kwargs):
        return self.request("get", url, **kwargs)

    def post(self, url, data=None, **kwargs):
        return self.request("post", url, data=data, **kwargs)
