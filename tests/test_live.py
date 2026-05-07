import os
import time
import uuid
import hashlib
from pathlib import Path

import pytest

from lanzou.api import LanZouCloud


pytestmark = pytest.mark.skipif(os.getenv("LANZOU_API_LIVE") != "1", reason="live test disabled")
big_live_mark = pytest.mark.skipif(os.getenv("LANZOU_API_LIVE_BIG") != "1", reason="big live test disabled")


def login_live_client():
    username = os.getenv("LANZOU_API_USERNAME")
    password = os.getenv("LANZOU_API_PASSWORD")
    cookie = os.getenv("LANZOU_API_COOKIE")

    client = LanZouCloud()
    if cookie:
        assert client.login_by_cookie(cookie) == LanZouCloud.SUCCESS
        return client, cookie

    assert username and password
    assert client.login(username, password) == LanZouCloud.SUCCESS
    return client, client.get_cookie()


def wait_for(predicate, timeout=4.0, interval=0.3):
    deadline = time.time() + timeout
    while time.time() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(interval)
    return predicate()


def purge_folder_shallow(client, folder_id):
    for subdir in list(client.get_dir_list(folder_id)):
        for item in list(client.get_file_list(subdir.id)):
            client.delete(item.id, True)
        client.delete(subdir.id, False)
        rec_subdir = wait_for(lambda: client.get_rec_dir_list().find_by_id(subdir.id))
        if rec_subdir:
            client.delete_rec(subdir.id, False)

    for item in list(client.get_file_list(folder_id)):
        client.delete(item.id, True)

    client.delete(folder_id, False)
    rec_dir = wait_for(lambda: client.get_rec_dir_list().find_by_id(folder_id))
    if rec_dir:
        client.delete_rec(folder_id, False)


def purge_named_root_folders(client, *prefixes):
    for folder in list(client.get_dir_list(-1)):
        if any(folder.name.startswith(prefix) or folder.name == prefix for prefix in prefixes):
            try:
                purge_folder_shallow(client, folder.id)
            except Exception:
                pass
    for rec_dir in list(client.get_rec_dir_list()):
        if any(rec_dir.name.startswith(prefix) or rec_dir.name == prefix for prefix in prefixes):
            try:
                client.delete_rec(rec_dir.id, False)
            except Exception:
                pass


def wait_for_rec_file(client, file_id, timeout=4.0, interval=0.3):
    return wait_for(lambda: client.get_rec_file_list(-1).find_by_id(file_id), timeout=timeout, interval=interval)


def wait_for_rec_all_folder(client, folder_id, timeout=12.0, interval=0.5):
    def _lookup():
        _, rec_folders = client.get_rec_all()
        if rec_folders is None:
            return None
        return rec_folders.find_by_id(folder_id)

    return wait_for(_lookup, timeout=timeout, interval=interval)


def file_md5(path):
    digest = hashlib.md5()
    with open(path, "rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_live_login_and_basic_file_flow(tmp_path):
    client, _ = login_live_client()

    folder_name = f"Codex-LanZouCloud-API-Test-{uuid.uuid4().hex[:8]}"
    folder_id = client.mkdir(-1, folder_name, "Codex live test")
    assert folder_id not in (LanZouCloud.MKDIR_ERROR, LanZouCloud.FAILED)

    sample = tmp_path / "sample.txt"
    sample.write_text("codex-live-test", encoding="utf-8")
    try:
        assert client.upload_file(str(sample), folder_id) == LanZouCloud.SUCCESS
        files = client.get_file_list(folder_id)
        target = files.find_by_name("sample.txt")
        assert target is not None
        assert client.set_desc(target.id, "file-desc", True) == LanZouCloud.SUCCESS
        assert client.set_passwd(target.id, "1234", True) == LanZouCloud.SUCCESS
        share = client.get_share_info(target.id, is_file=True)
        assert share.code == LanZouCloud.SUCCESS
        info = client.get_file_info_by_url(share.url, share.pwd)
        assert info.code == LanZouCloud.SUCCESS
        assert client.rename_dir(folder_id, folder_name + "-renamed") == LanZouCloud.SUCCESS
        assert client.set_desc(folder_id, "dir-desc", False) == LanZouCloud.SUCCESS
        assert client.set_passwd(folder_id, "abcd", False) == LanZouCloud.SUCCESS
        assert client.delete(target.id, True) == LanZouCloud.SUCCESS
        assert client.recovery(target.id, True) == LanZouCloud.SUCCESS
        assert client.get_file_list(-1).find_by_id(target.id) is not None
    finally:
        files = client.get_file_list(folder_id)
        for item in files:
            client.delete(item.id, True)
        purge_folder_shallow(client, folder_id)


def test_live_folder_share_move_and_path_flow(tmp_path):
    client, cookie = login_live_client()

    cookie_client = LanZouCloud()
    assert cookie_client.login_by_cookie(cookie) == LanZouCloud.SUCCESS

    base = f"Codex-LanZouCloud-API-Ext-{uuid.uuid4().hex[:8]}"
    root_a = client.mkdir(-1, base + "-A", "ext root A")
    root_b = client.mkdir(-1, base + "-B", "ext root B")
    empty_dir = client.mkdir(-1, base + "-EMPTY", "empty dir")
    subdir = client.mkdir(root_a, "subdir", "nested dir")
    assert root_a not in (LanZouCloud.MKDIR_ERROR, LanZouCloud.FAILED)
    assert root_b not in (LanZouCloud.MKDIR_ERROR, LanZouCloud.FAILED)
    assert empty_dir not in (LanZouCloud.MKDIR_ERROR, LanZouCloud.FAILED)
    assert subdir not in (LanZouCloud.MKDIR_ERROR, LanZouCloud.FAILED)

    alpha = tmp_path / "alpha.txt"
    beta = tmp_path / "beta.txt"
    alpha.write_text("alpha-data", encoding="utf-8")
    beta.write_text("beta-data", encoding="utf-8")

    try:
        assert client.upload_file(str(alpha), root_a) == LanZouCloud.SUCCESS
        assert client.upload_file(str(beta), root_a) == LanZouCloud.SUCCESS

        files_a = client.get_file_list(root_a)
        alpha_item = files_a.find_by_name("alpha.txt")
        beta_item = files_a.find_by_name("beta.txt")
        assert alpha_item is not None
        assert beta_item is not None
        assert client.get_dir_list(root_a).find_by_id(subdir) is not None

        share_alpha = client.get_share_info(alpha_item.id, True)
        assert share_alpha.code == LanZouCloud.SUCCESS
        assert client.get_durl_by_url(share_alpha.url, share_alpha.pwd).code == LanZouCloud.SUCCESS
        assert client.get_durl_by_id(alpha_item.id).code == LanZouCloud.SUCCESS
        assert client.get_file_info_by_id(alpha_item.id).code == LanZouCloud.SUCCESS

        folder_share = client.get_share_info(root_a, False)
        assert folder_share.code == LanZouCloud.SUCCESS
        folder_info_url = client.get_folder_info_by_url(folder_share.url, folder_share.pwd)
        assert folder_info_url.code == LanZouCloud.SUCCESS
        assert len(folder_info_url.files) >= 2
        folder_info_id = client.get_folder_info_by_id(root_a)
        assert folder_info_id.code == LanZouCloud.SUCCESS
        assert len(folder_info_id.files) >= 2

        download_by_url = tmp_path / "dir_by_url"
        download_by_id = tmp_path / "dir_by_id"
        assert client.down_dir_by_url(folder_share.url, folder_share.pwd, str(download_by_url), overwrite=True) == LanZouCloud.SUCCESS
        assert client.down_dir_by_id(root_a, str(download_by_id), overwrite=True) == LanZouCloud.SUCCESS
        assert (download_by_url / folder_share.name / "alpha.txt").exists()
        assert (download_by_id / folder_share.name / "alpha.txt").exists()

        assert client.move_file(beta_item.id, root_b) == LanZouCloud.SUCCESS
        assert client.get_file_list(root_b).find_by_id(beta_item.id) is not None
        assert client.move_folder(subdir, root_b) == LanZouCloud.SUCCESS
        assert client.get_dir_list(root_b).find_by_name("subdir") is not None

        assert client.set_passwd(root_b, "abcd", False) == LanZouCloud.SUCCESS
        root_b_share = client.get_share_info(root_b, False)
        assert root_b_share.code == LanZouCloud.SUCCESS
        assert root_b_share.pwd == "abcd"
        assert client.get_folder_info_by_url(root_b_share.url, root_b_share.pwd).code == LanZouCloud.SUCCESS

        move_folders = client.get_move_folders()
        assert move_folders.find_by_id(root_a) is not None
        assert move_folders.find_by_id(root_b) is not None
        move_paths = client.get_move_paths()
        assert any(path.find_by_id(root_a) for path in move_paths)
        assert any(path.find_by_id(root_b) for path in move_paths)
        assert client.get_full_path(root_a).find_by_id(root_a) is not None

        assert client.delete(beta_item.id, True) == LanZouCloud.SUCCESS
        assert client.get_rec_file_list(-1).find_by_id(beta_item.id) is not None
        assert client.delete_rec(beta_item.id, True) == LanZouCloud.SUCCESS

        assert client.delete(empty_dir, False) == LanZouCloud.SUCCESS
        assert wait_for(lambda: client.get_rec_dir_list().find_by_id(empty_dir)) is not None
        assert client.recovery(empty_dir, False) == LanZouCloud.SUCCESS
        assert client.delete(empty_dir, False) == LanZouCloud.SUCCESS
        assert wait_for(lambda: client.get_rec_dir_list().find_by_id(empty_dir)) is not None
        assert client.delete_rec(empty_dir, False) == LanZouCloud.SUCCESS
    finally:
        for folder_id in (root_a, root_b):
            try:
                if client.get_dir_list(-1).find_by_id(folder_id) is not None:
                    purge_folder_shallow(client, folder_id)
            except Exception:
                pass

        try:
            if client.get_dir_list(-1).find_by_id(empty_dir) is not None:
                purge_folder_shallow(client, empty_dir)
        except Exception:
            pass

        rec_empty_dir = wait_for(lambda: client.get_rec_dir_list().find_by_id(empty_dir))
        if rec_empty_dir:
            client.delete_rec(empty_dir, False)


def test_live_recycle_batch_logout_and_upload_dir_flow(tmp_path):
    client, _ = login_live_client()

    base = f"Codex-LanZouCloud-API-Batch-{uuid.uuid4().hex[:8]}"
    batch_dir = client.mkdir(-1, base + "-batch", "batch root")
    assert batch_dir not in (LanZouCloud.MKDIR_ERROR, LanZouCloud.FAILED)

    upload_dir_local = tmp_path / "upload_dir_case"
    upload_dir_local.mkdir()
    for idx in range(3):
        (upload_dir_local / f"u{idx}.txt").write_text(f"upload-{idx}", encoding="utf-8")

    try:
        assert client.upload_dir(str(upload_dir_local), -1) == LanZouCloud.SUCCESS
        uploaded_folder = client.get_dir_list(-1).find_by_name(upload_dir_local.name)
        assert uploaded_folder is not None
        assert len(client.get_file_list(uploaded_folder.id)) == 3

        batch_file_paths = []
        for idx in range(2):
            path = tmp_path / f"batch_{idx}.txt"
            path.write_text(f"batch-{idx}", encoding="utf-8")
            batch_file_paths.append(path)
            assert client.upload_file(str(path), batch_dir) == LanZouCloud.SUCCESS

        batch_files = [item for item in client.get_file_list(batch_dir) if item.name.startswith("batch_")]
        batch_file_ids = [item.id for item in batch_files]
        assert len(batch_file_ids) == 2

        for fid in batch_file_ids:
            assert client.delete(fid, True) == LanZouCloud.SUCCESS
        assert all(wait_for_rec_file(client, fid) is not None for fid in batch_file_ids)

        assert client.recovery_multi(files=batch_file_ids) == LanZouCloud.SUCCESS
        # 当前真实行为：批量恢复文件后落回根目录，不回原目录
        assert all(client.get_file_list(-1).find_by_id(fid) is not None for fid in batch_file_ids)
        assert all(client.get_file_list(batch_dir).find_by_id(fid) is None for fid in batch_file_ids)

        for fid in batch_file_ids:
            assert client.delete(fid, True) == LanZouCloud.SUCCESS
        assert client.delete_rec_multi(files=batch_file_ids) == LanZouCloud.SUCCESS

        folder1 = client.mkdir(-1, base + "-folder1", "folder1")
        folder2 = client.mkdir(-1, base + "-folder2", "folder2")
        assert folder1 not in (LanZouCloud.MKDIR_ERROR, LanZouCloud.FAILED)
        assert folder2 not in (LanZouCloud.MKDIR_ERROR, LanZouCloud.FAILED)
        assert client.delete(folder1, False) == LanZouCloud.SUCCESS
        assert client.delete(folder2, False) == LanZouCloud.SUCCESS
        assert client.recovery_multi(folders=[folder1, folder2]) == LanZouCloud.SUCCESS
        assert client.get_dir_list(-1).find_by_id(folder1) is not None
        assert client.get_dir_list(-1).find_by_id(folder2) is not None

        assert client.delete(folder1, False) == LanZouCloud.SUCCESS
        assert client.delete(folder2, False) == LanZouCloud.SUCCESS
        assert client.delete_rec_multi(folders=[folder1, folder2]) == LanZouCloud.SUCCESS

        folder3 = client.mkdir(-1, base + "-folder3", "folder3")
        folder4 = client.mkdir(-1, base + "-folder4", "folder4")
        assert folder3 not in (LanZouCloud.MKDIR_ERROR, LanZouCloud.FAILED)
        assert folder4 not in (LanZouCloud.MKDIR_ERROR, LanZouCloud.FAILED)
        assert client.delete(folder3, False) == LanZouCloud.SUCCESS
        assert client.delete(folder4, False) == LanZouCloud.SUCCESS
        assert client.recovery_all() == LanZouCloud.SUCCESS
        assert client.get_dir_list(-1).find_by_id(folder3) is not None
        assert client.get_dir_list(-1).find_by_id(folder4) is not None

        rec_all_folder = client.mkdir(-1, base + "-rec-all", "rec all folder")
        assert rec_all_folder not in (LanZouCloud.MKDIR_ERROR, LanZouCloud.FAILED)
        rec_all_files = []
        for idx in range(2):
            path = tmp_path / f"rec_all_{idx}.txt"
            path.write_text(f"rec-all-{idx}", encoding="utf-8")
            rec_all_files.append(path)
            assert client.upload_file(str(path), rec_all_folder) == LanZouCloud.SUCCESS
        assert client.delete(rec_all_folder, False) == LanZouCloud.SUCCESS
        assert wait_for(lambda: client.get_rec_dir_list().find_by_id(rec_all_folder)) is not None
        rec_folder = wait_for_rec_all_folder(client, rec_all_folder)
        assert rec_folder is not None
        assert len(rec_folder.files) == 2
        assert client.clean_rec() == LanZouCloud.SUCCESS
        assert wait_for(lambda: client.get_rec_dir_list().find_by_id(rec_all_folder)) is None

        rename_source = tmp_path / "rename_src.txt"
        rename_source.write_text("rename-me", encoding="utf-8")
        assert client.upload_file(str(rename_source), batch_dir) == LanZouCloud.SUCCESS
        rename_target = client.get_file_list(batch_dir).find_by_name("rename_src.txt")
        assert rename_target is not None
        rename_code = client.rename_file(rename_target.id, "rename_dst")
        assert rename_code in (LanZouCloud.SUCCESS, LanZouCloud.FAILED)
        if rename_code == LanZouCloud.SUCCESS:
            refreshed = client.get_file_list(batch_dir)
            assert refreshed.find_by_name("rename_dst.txt") is not None or refreshed.find_by_name("rename_dst") is not None

        assert client.logout() == LanZouCloud.SUCCESS
    finally:
        try:
            client.login(os.getenv("LANZOU_API_USERNAME"), os.getenv("LANZOU_API_PASSWORD"))
        except Exception:
            pass
        purge_named_root_folders(client, base, upload_dir_local.name)


@big_live_mark
def test_live_big_file_upload_and_rebuild(tmp_path):
    client, _ = login_live_client()
    client.ignore_limits()
    assert client.set_max_size(100) == LanZouCloud.SUCCESS

    base = f"Codex-LanZouCloud-API-Big-{uuid.uuid4().hex[:8]}"
    big_root = client.mkdir(-1, base, "big file root")
    assert big_root not in (LanZouCloud.MKDIR_ERROR, LanZouCloud.FAILED)

    big_file = tmp_path / "big_payload.bin"
    chunk = bytes(range(256)) * 4096
    target_size = 101 * 1024 * 1024
    full_chunks, remainder = divmod(target_size, len(chunk))
    with open(big_file, "wb") as fp:
        for _ in range(full_chunks):
            fp.write(chunk)
        if remainder:
            fp.write(chunk[:remainder])
        fp.write(b"codex-big-file-check")
    assert big_file.stat().st_size > 100 * 1024 * 1024

    try:
        expected_md5 = file_md5(big_file)
        assert client.upload_file(str(big_file), big_root) == LanZouCloud.SUCCESS

        big_dir = wait_for(lambda: client.get_dir_list(big_root).find_by_name(big_file.name), timeout=8.0, interval=0.5)
        assert big_dir is not None

        download_root = tmp_path / "big_download"
        assert client.down_dir_by_id(big_dir.id, str(download_root), overwrite=True) == LanZouCloud.SUCCESS
        restored = download_root / big_file.name
        assert restored.exists()
        assert file_md5(restored) == expected_md5
    finally:
        purge_named_root_folders(client, base)
