from lanzou.api._internal.auth import looks_logged_in, parse_cookie_input


def test_parse_cookie_input_from_string():
    cookie = parse_cookie_input("ylogin=123; phpdisk_info=abc; PHPSESSID=xyz")
    assert cookie["ylogin"] == "123"
    assert cookie["phpdisk_info"] == "abc"
    assert cookie["PHPSESSID"] == "xyz"


def test_parse_cookie_input_from_dict():
    cookie = parse_cookie_input({"ylogin": "123"})
    assert cookie == {"ylogin": "123"}


def test_looks_logged_in():
    assert looks_logged_in("<html>User's Control Panel</html>")
    login_page = '<input placeholder="用户名/账号"><input placeholder="输入密码"><input onclick="uselogin(1);">'
    assert not looks_logged_in(login_page)
