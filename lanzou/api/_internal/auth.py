from urllib.parse import urljoin

from lanzou.api._internal.http import build_browser_headers, share_origin

LOGIN_PAGE_URL = "https://accounts.woozooo.com/accounts.php?action=login&ref=pc.woozooo.com"
LOGIN_POST_URL = "https://accounts.woozooo.com/accounts.php"
MYDISK_VERIFY_URL = "https://pc.woozooo.com/mydisk.php?item=files&action=index"
LOGOUT_URL = "https://pc.woozooo.com/account.php?action=logout"


def parse_cookie_input(cookie):
    if isinstance(cookie, dict):
        return dict(cookie)
    if isinstance(cookie, str):
        pairs = [part.strip() for part in cookie.split(";") if "=" in part]
        return {name.strip(): value.strip() for name, value in (pair.split("=", 1) for pair in pairs)}
    return {}


def looks_logged_in(html_text):
    if "User's Control Panel" in html_text:
        return True
    if "用户名/账号" in html_text and "onclick=\"uselogin(1);\"" in html_text:
        return False
    if "网盘用户登录" in html_text:
        return False
    return True


def login_with_password(http_client, username, password):
    login_page = http_client.get(
        LOGIN_PAGE_URL,
        allow_acw_retry=True,
        headers=build_browser_headers(http_client.headers, referer="https://pc.woozooo.com/"),
    )
    if not login_page:
        return None

    login_api_headers = build_browser_headers(
        http_client.headers,
        referer=login_page.url,
        origin=share_origin(login_page.url),
        extra={"X-Requested-With": "XMLHttpRequest"},
    )
    login_resp = http_client.post(
        LOGIN_POST_URL,
        {"task": "uselogin", "username": username, "password": password},
        headers=login_api_headers,
    )
    if not login_resp:
        return None

    try:
        payload = login_resp.json()
    except ValueError:
        return None

    if str(payload.get("zt")) != "1":
        return payload

    redirect_url = urljoin(login_resp.url, payload.get("msgs", ""))
    http_client.get(
        redirect_url,
        allow_redirects=True,
        headers=build_browser_headers(http_client.headers, referer=login_page.url),
    )
    verify_resp = http_client.get(
        MYDISK_VERIFY_URL,
        headers=build_browser_headers(http_client.headers, referer="https://pc.woozooo.com/mydisk.php"),
    )
    return payload, verify_resp


def verify_cookie_login(http_client, cookie):
    cookie_dict = parse_cookie_input(cookie)
    if not cookie_dict:
        return False, None

    http_client.session.cookies.update(cookie_dict)
    verify_resp = http_client.get(
        MYDISK_VERIFY_URL,
        headers=build_browser_headers(http_client.headers, referer="https://pc.woozooo.com/mydisk.php"),
    )
    if not verify_resp:
        return False, None
    return looks_logged_in(verify_resp.text), verify_resp
