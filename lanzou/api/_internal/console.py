import re


def parse_console_dynamic_values(html_text):
    values = {}
    vei_match = re.search(r"'vei':'([^']+)'", html_text)
    if vei_match:
        values["vei"] = vei_match.group(1)
    uid_match = re.search(r"url\s*:\s*'/doupload\.php\?uid=(\d+)'", html_text)
    if uid_match:
        values["uid"] = uid_match.group(1)
    return values
