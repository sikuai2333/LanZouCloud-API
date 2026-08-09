# Changelog

## `v2.6.12` - `2026-08-09`

- 修复下载直链解析遇到 CDN `acw_sc__v2` JS 反爬挑战时抛出 `KeyError: 'location'`、所有文件下载失败的问题：`get_file_info_by_url()` 请求假直链（`fake_url`）时启用 `allow_acw_retry=True`，自动计算 `acw_sc__v2` cookie 后重试
- 增强 `_should_retry_with_acw()` 挑战识别：同时匹配 `acw_sc__v2` 变量与 `arg1='...'` 特征，避免 CDN 变更挑战页面结构后检测失效
- 实测 `wwbln.lanzouw.com` / `wwbfe.lanzouq.com` 等域名下的分享文件下载均可稳定通过挑战

## `v2.6.11` - `2026-05-07`

- 重建当前蓝奏网页登录流程，恢复 `login(username, password)`，并保留 `login_by_cookie(cookie)` 作为稳定登录路径
- 统一请求层，修复当前站点下的域名切换、Referer / Origin、Cookie 验证与分享页 AJAX 派生逻辑
- 修复分享文件、带提取码分享文件、分享文件夹、直链、控制台文件列表、`get_full_path()`、`get_move_folders()`、`get_move_paths()`、回收站与批量回收相关接口
- 新增单元测试与 live 测试，已覆盖登录、上传下载、分享解析、移动、回收站、`upload_dir()`、`logout()` 等主要流程
- 明确 `rename_file()` 的真实行为：该接口受蓝奏会员能力限制，当前非会员账号实测服务端返回 `此功能仅会员使用，请先开通会员`，本库返回 `FAILED`
- 已实测在 `ignore_limits()` + `set_max_size(100)` 条件下，101 MiB 文件可成功分片上传，并可通过 `down_dir_by_id()` 完整重组下载，MD5 一致
- 补充现代 Python 打包元数据，新增 `pyproject.toml`、`python_requires`、项目链接与更明确的包描述
- 在 README 中补充安装方式、快速开始、adapter 层使用边界与已知限制，便于作为网页后端底层 SDK 集成

## Notes

- 历史版本更新日志暂时仍完整保留在 `README.md`
