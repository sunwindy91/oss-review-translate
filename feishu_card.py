#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""feishu_card.py — 把 summary.json 变成飞书交互卡片 JSON **和**一条可粘贴的命令。

为什么**不自动发**：给群发消息是**对外、不可逆**的动作（发出去撤不回、会打扰人）。
所以本工具只做"生成 + 打印命令"，由人在确认后自己执行。这也是本项目的一贯立场：
阅读可以自动化，**表态不行**。

用法：
  python oss-review-translate.py ... --format json     # 先产出 summary.json
  python feishu_card.py out/summary.json --out out/feishu_card.json
  # 然后手工执行它打印出来的那条 curl（或把它贴进任意支持 webhook 的地方）
"""
import argparse
import json
import sys


def build_card(summary: dict) -> dict:
    c = summary.get("counts", {})
    title = f"审阅待确认 · {summary.get('repo', '?')}#{summary.get('number', '?')}"
    title_text = summary.get("title", "")
    if len(title_text) > 90:
        title_text = title_text[:90].rsplit(" ", 1)[0] + "…"
    lines = [
        f"**{title_text}**",
        "",
        # 总数优先用 total_paragraphs（有风险的段落只是其中一个子集）
        f"段落 {summary.get('total_paragraphs', len(summary.get('paragraphs', [])))} · "
        f"**高风险 {c.get('high', 0)}** · 中 {c.get('medium', 0)} · 低 {c.get('low', 0)}",
        "",
    ]
    for para in summary.get("paragraphs", []):
        highs = [f["text"] for f in para.get("flags", []) if f.get("level") == "high"]
        if highs:
            lines.append(f"- `[{para['tag']}]` " + "；".join(highs)[:120])
    lines += ["", f"[在原帖查看]({summary.get('url', '')})", "",
              "_风险未确认前不要回帖（回帖不可逆）。_"]
    return {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": title}, "template": "blue"},
            "elements": [{"tag": "markdown", "content": "\n".join(lines)}],
        },
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="summary.json → 飞书卡片 JSON（不自动发送）")
    ap.add_argument("summary")
    ap.add_argument("--out", default=None, help="卡片 JSON 输出路径")
    ap.add_argument("--webhook-env", default="FEISHU_WEBHOOK", help="从哪个环境变量取 webhook（只用于打印命令）")
    a = ap.parse_args(argv)
    summary = json.loads(open(a.summary, encoding="utf-8").read())
    card = build_card(summary)
    text = json.dumps(card, ensure_ascii=False, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("  已生成卡片 JSON → " + a.out)
    else:
        print(text)
    print("\n# 确认要发到群里时，自己执行（本工具不会自动发送）：")
    print(f'#   curl -sS -X POST -H "Content-Type: application/json" \\')
    print(f'#     -d @{a.out or "card.json"} "$%{a.webhook_env}%"')
    print("\n  为什么停在这里：群消息是对外不可逆动作；阅读可自动，表态不行。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
