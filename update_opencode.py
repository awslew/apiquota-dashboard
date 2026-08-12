# -*- coding: utf-8 -*-
"""更新 OpenCode Go 的 cookie 与用量页地址（换账号 / cookie 过期刷新 用）。

用法（在项目根目录下）：
  python update_opencode.py "<新cookie>" "<新用量页URL>"

示例：
  python update_opencode.py "oc_locale=zh; auth=Fe26.2**...." "https://opencode.ai/workspace/wrk_XXXX/go"

只改 config.yaml 里的 opencode_go.cookie 和 usage_url 两行，保留其余配置与注释。
改完需重启应用生效：托盘右键「退出」，再运行  python main.py。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CFG = ROOT / "config.yaml"


def set_line(text: str, key: str, value: str) -> str:
    """按 key 替换行（保留缩进与其它行），值用 YAML 双引号包裹。"""
    out = []
    for ln in text.split("\n"):
        if re.match(rf"^\s*{re.escape(key)}:", ln):
            indent = ln[: len(ln) - len(ln.lstrip())]
            out.append(f'{indent}{key}: "{value}"')
        else:
            out.append(ln)
    return "\n".join(out)


def main():
    if len(sys.argv) < 3:
        print('用法: python update_opencode.py "<cookie>" "<usage_url>"')
        return 1
    cookie, url = sys.argv[1], sys.argv[2]
    if '"' in cookie or "\\" in cookie:
        print("[错误] cookie 里不能包含双引号或反斜杠，请重新复制。")
        return 1

    text = CFG.read_text(encoding="utf-8")
    new_text = set_line(set_line(text, "cookie", cookie), "usage_url", url)
    if new_text == text:
        print("[警告] 未找到可替换的 cookie/usage_url 行，请检查 config.yaml。")
        return 1
    CFG.write_text(new_text, encoding="utf-8")
    print("[update_opencode] 已更新 config.yaml：")
    print(f"  cookie   = {cookie[:18]}...")
    print(f"  usage_url = {url}")
    print("重启应用生效：托盘右键「退出」→ 再运行  python main.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
