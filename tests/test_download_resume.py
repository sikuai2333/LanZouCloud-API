import pickle
from pathlib import Path

import requests

from lanzou.api import LanZouCloud
from lanzou.api.models import FileList
from lanzou.api.types import DirectUrlInfo, File


class FakeResponse:
    def __init__(self, chunks=None, status_code=206):
        self._chunks = list(chunks or [])
        self.status_code = status_code

    def iter_content(self, chunk_size):
        for chunk in self._chunks:
            if isinstance(chunk, Exception):
                raise chunk
            yield chunk

    def close(self):
        return None


def test_stream_download_retries_after_chunk_error(tmp_path):
    client = LanZouCloud()
    attempts = []
    responses = [
        FakeResponse([b"abc", requests.exceptions.ChunkedEncodingError("broken")]),
        FakeResponse([b"def"]),
    ]

    def fake_get(url, **kwargs):
        attempts.append(kwargs.get("headers", {}).get("Range"))
        return responses.pop(0)

    client._get = fake_get

    target = tmp_path / "target.bin"
    with target.open("ab") as fp:
        success, downloaded = client._stream_download("https://d.test/file", fp, start_byte=0)

    assert success is True
    assert downloaded == 6
    assert target.read_bytes() == b"abcdef"
    assert attempts == [None, "bytes=3-"]


def test_down_big_file_resumes_from_part_offset(tmp_path):
    client = LanZouCloud()
    save_path = tmp_path / "downloads"
    save_path.mkdir()
    big_file = save_path / "big.bin"
    big_file.write_bytes(b"hello")
    record = big_file.with_suffix(".bin.record")
    with record.open("wb") as rf:
        pickle.dump({"last_ending": 0, "finished": [], "part_name": "part1", "part_offset": 5}, rf, protocol=4)

    ranges = []

    def fake_get_durl_by_id(fid):
        return DirectUrlInfo(LanZouCloud.SUCCESS, f"https://d.test/{fid}", "part")

    def fake_stream_download(url, file_handle, *, start_byte=0, callback=None, total_size=None, file_name=None, max_retries=5):
        ranges.append(start_byte)
        file_handle.write(b" world")
        file_handle.flush()
        if callback is not None:
            callback(file_name, total_size, start_byte + 6)
        return True, start_byte + 6

    client.get_durl_by_id = fake_get_durl_by_id
    client._stream_download = fake_stream_download

    parts = FileList()
    parts.append(File(name="part1", id=1, time="2026-05-07", size="5 M", type="bin", downs=0, has_pwd=False, has_des=False))
    code = client._down_big_file("big.bin", 11, parts, str(save_path), overwrite=True)

    assert code == LanZouCloud.SUCCESS
    assert ranges == [5]
    assert big_file.read_bytes() == b"hello world"
    assert not record.exists()
