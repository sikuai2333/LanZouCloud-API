import re
from urllib.parse import urljoin

from lanzou.api._internal.http import join_share_url, share_origin
from lanzou.api.utils import remove_notes


def _parse_js_variables(html):
    return {name: value for name, value in re.findall(r"var\s+([A-Za-z_]\w*)\s*=\s*'([^']*)';", html)}


def _parse_js_object_pairs(block, variables):
    pairs = {}
    for key, raw_value in re.findall(r"['\"](\w+)['\"]\s*:\s*([^,\n}]+)", block):
        value = raw_value.strip()
        if value in variables:
            value = variables[value]
        value = value.strip().strip("'\"")
        pairs[key] = value
    return pairs


def parse_folder_page_context(html_text, share_url, response_url):
    html = remove_notes(html_text)
    origin = share_origin(response_url or share_url)
    referer = response_url or share_url
    variables = _parse_js_variables(html)

    context = {
        "html": html,
        "origin": origin,
        "referer": referer,
        "ajax_url": join_share_url(origin + "/", "filemoreajax.php"),
    }
    ajax_match = re.search(
        r"url\s*:\s*['\"]([^'\"]*filemoreajax\.php\?file=\d+)['\"].*?data\s*:\s*\{(.*?)\}\s*,\s*dataType",
        html,
        re.S,
    )
    data_pairs = _parse_js_object_pairs(ajax_match.group(2), variables) if ajax_match else {}
    if ajax_match:
        context["ajax_url"] = join_share_url(origin + "/", ajax_match.group(1).lstrip("/"))

    context["lx"] = data_pairs.get("lx") or re.findall(r"'lx':'?(\d)'?,", html)[0]
    context["t"] = data_pairs.get("t") or re.findall(r"var\s+[A-Za-z_]\w*\s*=\s*'(\d{10})';", html)[0]
    context["k"] = data_pairs.get("k") or re.findall(r"var\s+[A-Za-z_]\w*\s*=\s*'([0-9a-z]{15,})';", html)[0]
    context["folder_id"] = data_pairs.get("fid") or re.findall(r"'fid':'?(\d+)'?,", html)[0]
    for key in ("uid", "rep", "up", "ls"):
        if key in data_pairs:
            context[key] = data_pairs[key]

    title_var_match = re.search(r"document\.title\s*=\s*([A-Za-z_]\w*)", html)
    folder_name = None
    if title_var_match:
        folder_name = variables.get(title_var_match.group(1))
    if not folder_name:
        folder_name = (
            re.findall(r"var.+?='(.+?)';\n.+document.title", html)
            or re.findall(r'<div class="user-title">(.+?)</div>', html)
        )[0]
    context["folder_name"] = folder_name
    time_match = re.findall(r'class="rets">([\d\-]+?)<a', html)
    context["folder_time"] = time_match[0] if time_match else ""
    desc_match = re.findall(r'id="filename">(.+?)</span>', html) or re.findall(
        r'<div class="user-radio-\d"></div>(.+?)</div>', html
    )
    context["folder_desc"] = desc_match[0] if desc_match else ""
    return context


def parse_file_page_context(html_text, share_url, response_url):
    html = remove_notes(html_text)
    origin = share_origin(response_url or share_url)
    referer = response_url or share_url
    return {
        "html": html,
        "origin": origin,
        "referer": referer,
        "ajax_url": join_share_url(origin + "/", "ajaxm.php"),
    }


def resolve_iframe_url(context, iframe_src):
    return urljoin(context["origin"] + "/", iframe_src)


def resolve_sign_from_iframe(frame_html):
    sign = re.search(r"'sign':(.+?),", frame_html).group(1)
    sign = sign.strip().strip("'\"")
    if len(sign) < 20:
        sign = re.search(rf"var {sign}\s*=\s*'(.+?)';", frame_html).group(1)
    return sign


def parse_password_share_ajax(html):
    ajax_paths = re.findall(r"url\s*:\s*['\"]([^'\"]*ajaxm\.php\?file=\d+)['\"]", html)
    sign_matches = re.findall(r"['\"]sign['\"]\s*:\s*['\"]([^'\"]+)['\"]", html)

    sign = sign_matches[-1] if sign_matches else None
    if not sign:
        sign_var_matches = re.findall(r"['\"]sign['\"]\s*:\s*([A-Za-z_]\w*)", html)
        if sign_var_matches:
            sign_var = sign_var_matches[-1]
            sign_var_match = re.search(rf"var\s+{re.escape(sign_var)}\s*=\s*['\"](.+?)['\"];", html)
            if sign_var_match:
                sign = sign_var_match.group(1)

    kd_matches = re.findall(r"var\s+kdns\s*=\s*(\d+)\s*;", html)
    return {
        "ajax_path": ajax_paths[-1] if ajax_paths else None,
        "sign": sign,
        "kd": kd_matches[-1] if kd_matches else None,
    }
