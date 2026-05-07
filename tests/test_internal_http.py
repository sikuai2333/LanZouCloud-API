from lanzou.api._internal.http import build_browser_headers, expand_lanzou_urls, join_share_url, share_origin


def test_expand_lanzou_urls_preserves_subdomain():
    urls = expand_lanzou_urls("https://foo.lanzouo.com/bar")
    assert urls[0] == "https://foo.lanzouo.com/bar"
    assert "https://foo.lanzoux.com/bar" in urls
    assert "https://foo.lanzouw.com/bar" in urls


def test_expand_lanzou_urls_non_lanzou():
    assert expand_lanzou_urls("https://pc.woozooo.com/account.php") == ["https://pc.woozooo.com/account.php"]


def test_build_browser_headers():
    headers = build_browser_headers({"User-Agent": "UA"}, referer="https://a.test/x", origin="https://a.test")
    assert headers["User-Agent"] == "UA"
    assert headers["Referer"] == "https://a.test/x"
    assert headers["Origin"] == "https://a.test"


def test_share_origin_and_join():
    assert share_origin("https://sub.lanzoux.com/abc") == "https://sub.lanzoux.com"
    assert join_share_url("https://sub.lanzoux.com/", "filemoreajax.php") == "https://sub.lanzoux.com/filemoreajax.php"
