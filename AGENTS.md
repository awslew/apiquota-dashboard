# AGENTS.md

面向在此仓库工作的 coding agent。**只写"看代码不容易知道"的约束**。
项目介绍见 [README.md](./README.md)，数据源细节见 [docs/数据源确认.md](./docs/数据源确认.md)。

## 这是什么

Windows 托盘常驻的 **AI API 配额仪表盘**（Python，`pystray` + 纯标准库 `http.server`）：
把 DeepSeek / OpenRouter / OpenCode Go / Codex 四家的余额与窗口余量归一化成同一个模型，
后台定时刷新，浏览器页面展示。**所有数值直接来自官方数据源，不做任何推算。**

**改代码前必须理解的机制**：

1. **装配顺序是单向的**：`config.py` 加载归一化 → `QuotaStore`（`scheduler.py`，后台定时刷新）
   → `dashboard_ui/server.py` 起本地 HTTP → `dashboard_ui/tray.py` **阻塞**在托盘消息循环
   （托盘「退出」才返回），`finally` 里 `store.stop()` + `httpd.shutdown()`。
2. **数据真实性铁律（全仓最重要的一条）**：展示值必须来自官方响应。
   解析失败 / 未配置 / 非 200 / 无登录态 → 一律 `source_status = SOURCE_UNAVAILABLE`（「不可用」），
   **绝不硬编码、绝不编数字、绝不从本地端口或代理日志推算**。本次刷新失败但上次成功 →
   保留旧数据并置 `refresh_failed=True`（页面标「刷新失败·旧数据」）。
3. **端口是系统分配的，不是固定的**：`start_server()` 用
   `ThreadingHTTPServer(("127.0.0.1", 0), ...)`，启动后从 `httpd.server_address[1]` 取实际端口
   并打印。**本仓库的 `config.py` 里没有 `dashboard_port` 配置项，也没有 `API_QUOTA_PORT`
   之类的环境变量**——不要从别处同名组件的文档照抄一个"默认 8787"进来。要改端口语义，
   得先改 `config.py` + `config.example.yaml` + README 三处。
4. **配置缺失 = 直接退出（返回码 1）**，且会打印可复制的复制命令。配置默认路径是
   `PROJECT_ROOT/config.yaml`（`__file__` 解析，与 cwd / 盘符无关）。
   `main()` 的顺序是「先 load_config，再判断 `--selftest`」——**所以 `--selftest` 也必须有 config.yaml**。
5. **`~/.codex/auth.json` 只读**：`providers/codex.py` 读它拿 OAuth access_token，
   绝不写回、绝不改动 Codex 登录态。该文件缺失 / 401 / 非 200 → 「官方数据源不可用」。
6. **`pythonw` 下没有 stdout**：`main.py` 顶部的 `_ensure_stdio()` 会把 stdout/stderr 重定向到
   程序目录的 `dashboard.log`。无控制台运行时**日志只能看这个文件**；`print` 不能删。
7. **`os._exit(0)` 是有意的**：本会话若打开过浏览器仪表盘，Python 正常终结化会留下残留清理问题，
   所以最终统一跳终结化退出。不要"顺手"改成正常 `return`。
8. **日志脱敏是硬要求**：`config.mask_key()` 只输出前 6 位 + `***`。新增任何打印都要走脱敏。

## 常用命令

核实自 `main.py`（argparse）、`install_autostart.py`、`update_opencode.py` 与
`requirements.txt`（Windows + Python 3.9+，开发于 3.11）：

```bash
pip install -r requirements.txt
copy config.example.yaml config.yaml     # config.yaml 已 gitignore；bash: cp

python main.py                # 托盘 + 本地仪表盘（阻塞）
python main.py --selftest     # 无界面：跑一轮全量刷新，打印四家结果后退出（仍需 config.yaml）
python config.py              # 配置自检：打印已加载的 provider 与刷新间隔（key 已脱敏）

python install_autostart.py register|unregister|status
python update_opencode.py "<新cookie>" "<新用量页URL>"
```

本仓库**没有**单元测试套件、没有 lint 配置、没有构建步骤——改动靠
`python main.py --selftest`（需要真实配置与网络）与手工验证。不要凭空写
`npm test` / `pytest` 之类的命令到文档里。

## 改动纪律

**高风险区（改前先想清楚）**

- `providers/*.py` 的解析逻辑：官方响应改字段就会静默变「不可用」。**宁可如实报不可用，
  也不要写"猜一个值"的兜底**——这条铁律不许为了"页面好看"放松。
- `scheduler.py` 的失败降级：单家失败不能影响其他三家；`refresh_failed` 与
  `source_status` 是两个不同含义的字段（前者=本次失败沿用旧数据，后者=官方源本身不可用）。
- `dashboard_ui/server.py` 的路由表（`/`、`/app.css`、`/app.js`、`/api/quota`，其余 404）
  与 `/api/quota` 的 JSON 结构：前端 `app.js` 直接消费这些字段名。
- `config.py` 的归一化：缺失字段补齐默认值、`refresh_interval_minutes` **至少 1 分钟**
  （防 0/负数把刷新变成死循环）。配置加载失败**返回 None 而不是抛异常**，是调用方的分支依赖。
- `dashboard_ui/window.py`：打开页面前先 `store.refresh_now()`（强制刷新）再 `webbrowser.open`，
  且在后台 daemon 线程里做——不要挪到主线程阻塞托盘。
- `providers/openrouter.py`、`providers/opencode_go.py`、`providers/codex.py` 的 `proxy` 字段：
  海外接口靠它。别把代理写死成某个本机端口，默认值必须允许留空。

**已知取舍：不要"修"**

- **OpenCode Go 没有公开的用量查询 API**，唯一官方用量源是登录态控制台页（cookie + usage_url）。
  这是官方限制，不是没做的功能；cookie 过期就重新复制一份，`update_opencode.py` 是为这个场景写的。
- **DeepSeek 官方 API 不提供「今日用量」**：`today_usage` 为 `None` 是正确状态，别造数据。
- **`chatgpt.com` 会间歇性超时**：provider 内重试 + 调度器保留旧数据就是设计。
- **端口随系统分配**：每次启动端口可能不同，这是有意的（避免与本机其它服务抢端口），
  不是要"修"成固定端口。
- **托盘图标看不见**通常只是 Win11 把新图标收进溢出区。
- **平台是 Windows**：开机自启走 HKCU Run；不要为跨平台"顺手"改写自启实现。

**授权边界**

- `providers/codex.py` 的 Codex 配额方案**复刻自开源项目 steipete/CodexBar**
  （MIT，Copyright (c) 2026 Peter Steinberger）——归属行写在 **`providers/codex.py` 头部注释**
  与 **`docs/数据源确认.md`** 里，**不要删除或"整理"掉**。
- `docs/github-research.md` 末尾有调研参考项目的许可证表格，同样不要删。
- 本项目的 `LICENSE` 目前只有本项目自己的 MIT 版权行；若要补第三方归属，
  请**追加**而不是替换现有内容（改 LICENSE 前先跟维护者确认）。

## 目录 / 模块速览

| 路径 | 职责 |
|---|---|
| `main.py` | 入口：`_ensure_stdio()` → config → QuotaStore → 后台调度 → HTTP → 托盘；`--selftest` 分支 |
| `config.py` | 配置加载与归一化（`load_config` 失败返回 None）、`mask_key()` 脱敏、`__main__` 自检 |
| `scheduler.py` | `QuotaStore`：后台定时刷新、`refresh_now()` / `refresh_all()`、失败降级保留旧数据 |
| `providers/quota.py` | 统一数据模型：`Quota` / `WindowUsage` / `SOURCE_OK` / `SOURCE_UNAVAILABLE` |
| `providers/deepseek.py` | DeepSeek 官方余额（`/user/balance`，直连） |
| `providers/openrouter.py` | OpenRouter credits（余额 = total_credits − total_usage） |
| `providers/opencode_go.py` | OpenCode Go 登录态用量页解析（cookie + usage_url） |
| `providers/codex.py` | Codex `wham/usage`（读 `~/.codex/auth.json`，复刻自 CodexBar） |
| `dashboard_ui/server.py` | 本地 HTTP（`127.0.0.1` + 系统分配端口）+ `/api/quota` |
| `dashboard_ui/tray.py` | pystray 托盘（点击 → 打开仪表盘；右键 → 退出） |
| `dashboard_ui/window.py` | 强制刷新 + 用默认浏览器打开仪表盘 |
| `dashboard_ui/index.html` · `app.css` · `app.js` | 原生前端（无构建步骤） |
| `install_autostart.py` | 开机自启 register / unregister / status（HKCU Run） |
| `update_opencode.py` | 按 key 替换 config.yaml 里的 cookie / usage_url，保留其余行与注释 |
| `config.example.yaml` | 配置模板（含四家的字段与获取方式注释） |
| `docs/` | 数据源确认 / 调研记录 / 截图 |

## 不要做的事

- **不要提交 `config.yaml`**（真实 key / cookie）、`*.log`、`*.err`、`run.log` —— 全部已在 `.gitignore`。
- 不要在任何输出里打印完整 key / cookie / token（走 `mask_key()`）。
- 不要写回 `~/.codex/auth.json`，也不要读本地代理配置或日志来"推算"额度。
- 不要在缺少配置时用假数据 / 示例数字顶替，让页面看起来"有数据"。
- 不要引入新的第三方 Web 框架（前端是原生 HTML/CSS/JS，HTTP 是标准库）。
- 不要往 README / `llms.txt` / `AGENTS.md` 里写没核实过的命令、配置项或默认值
  （尤其是端口与"环境变量覆盖"这类容易从别处照抄错的细节）。
- 不要按镜像名批量杀进程（`taskkill /IM python.exe` 会误伤本机其它 Python 服务）；
  只按精确 PID。
