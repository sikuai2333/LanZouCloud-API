import json
import sys
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class DummyResponse(object):
    def __init__(self, text="", status_code=200, headers=None, json_data=None, url="https://example.test/"):
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}
        self._json_data = json_data
        self.url = url
        self.encoding = "utf-8"

    def json(self):
        if self._json_data is not None:
            return self._json_data
        return json.loads(self.text)


@pytest.fixture
def session():
    return requests.Session()
