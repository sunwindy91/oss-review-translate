#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""oss-review-translate — 开源协作里的"审阅级"双语保真工具（零依赖）

为什么不是又一个翻译器：机翻/LLM 翻译的失效点不在"词"，而在四件事——
  ① **对齐**：整段翻译后你无法逐句核对（原文↔译文必须逐段配对）
  ② **术语**：同一个词在不同段落译法漂移（allowance/sanction/dispatch…）
  ③ **义务强度**：规范文本里 must / must not / should / may 是四个不同强度，机翻常拉平
  ④ **回帖**：读错之后没有"确认环节"，错误会直接进入你的英文回复
本工具这四件事都做，且**不依赖任何模型**（确定性、可审计、可复现）。

用法：
  # 1) 拉一个 issue/PR 线程，生成双语对照骨架 + 风险标记
  python oss-review-translate.py --repo a2aproject/A2A --number 2250 --since 2026-10-14 --out out/

  # 2) 你已有两份译文（如 QQ 邮箱机翻 + 另一家），让工具**逐句比对**，标出分歧
  python oss-review-translate.py --repo a2aproject/A2A --number 2250 --since 2026-10-14 \
      --translation zh.txt --translation2 zh2.txt --out out/

  # 3) 生成英文"回帖确认"草稿（只引用高风险原句，不整段复述）
  #    同一条命令已生成 out/confirm.md

产物（out/）：
  bilingual.md  原文↔译文逐段对照，每段带 [P12] 编号与风险标记
  terms.md      术语表候选（未入库的技术名词）+ 你 glossary 的命中情况
  confirm.md    英文确认草稿（"Did I understand correctly: …"）
  audit.jsonl   一行审计记录（谁、何时、哪个线程、多少段、多少风险、用了几份译文）

术语库：`--glossary glossary.json`（或当前目录 .oss-translate/glossary.json）
  {"sanction": {"zh": "制裁/批准", "note": "本提案中指'人类对不可逆动作的批准'"},
   "allowance": {"zh": "额度", "note": "单次授权可用的次数预算"},
   "dispatch": {"zh": "派发", "note": "与 effect(效果) 区分"}}

设计原则（与 dsh-tool-meta 的治理一致）：
  · **原文永不丢**：任何译文都并排保留原文，且带段落编号可回指
  · **不确定就标出来**：义务强度/否定/数字/未入库术语，四种高风险信号显式列出
  · **回帖前先确认**：confirm.md 是"我这样理解对吗"的草稿，不是直接发出去的断言
  · **可审计**：audit.jsonl 记录这一次读的是哪一版、依据哪几份译文

诚实边界：
  · 它**不翻译**——译文由你（或机翻）提供；它保证的是"读得准、可核对、可回帖确认"。
  · 术语/风险检测是**启发式**（英文规范文本调校），不是语言学保证；发现漏检请提 issue。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------- 高风险信号

# 义务强度：规范语义的核心，机翻最常拉平的四组
MODAL_PATTERNS = [
    (r"\bMUST NOT\b", "禁止（MUST NOT）"),
    (r"\bSHALL NOT\b", "禁止（SHALL NOT）"),
    (r"\bMUST\b", "强制（MUST）"),
    (r"\bSHALL\b", "强制（SHALL）"),
    (r"\bshould not\b", "建议不（should not）"),
    (r"\bshould\b", "建议（should）"),
    (r"\bmay\b", "允许（may）"),
    (r"\bcan\b", "能力（can）"),
]
NEGATION = re.compile(r"\b(not|never|no|none|neither|nor|cannot|without)\b", re.I)
NUMBERS = re.compile(r"\b(one|two|three|zero|single|once|twice|first|second|exactly)\b|\b\d+\b", re.I)
CODE_SPAN = re.compile(r"`([^`]+)`")
SPEC_REF = re.compile(r"(§\s*\d+(?:\.\d+)*|\[[A-Z][A-Za-z]+\])")
# 这些词在提审/授权语境里几乎总有歧义，最适合放进术语库
TERM_HINTS = re.compile(
    r"\b(allowance|admission|admitted|sanction|sanctioned|steward|dispatch(?:ed)?|effect|"
    r"recovery|reconcile|reconciliation|idempotency|withdraw(?:al|n)?|supersede[sd]?|"
    r"outcome|receipt|attestation|conformance|oracle|binding|profile|extension|"
    r"precondition|reversibility|authenticity|auditability|escalation|revoke[sd]?|"
    r"spend|spent|reset|replenish|claim(?:ed|s)?)\b",
    re.I,
)


def fetch_thread(repo: str, number: int, since: str | None) -> dict:
    """用 gh 拉 issue/PR 线程（评论按时间排序，可按 since 过滤）。"""
    j = subprocess.run(
        ["gh", "issue", "view", str(number), "-R", repo, "--json", "title,body,state,url,comments"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if j.returncode != 0:
        # 可能是 PR
        j = subprocess.run(
            ["gh", "pr", "view", str(number), "-R", repo, "--json", "title,body,state,url,comments"],
            capture_output=True, text=True, encoding="utf-8",
        )
    if j.returncode != 0:
        raise SystemExit("gh 拉取失败：" + (j.stderr or j.stdout)[:300])
    data = json.loads(j.stdout)
    comments = []
    for c in data.get("comments", []):
        ts = c.get("createdAt") or ""
        if since and ts and ts < since:
            continue
        comments.append({"author": (c.get("author") or {}).get("login", "?"), "at": ts, "body": c.get("body") or ""})
    return {"title": data.get("title", ""), "body": data.get("body") or "", "state": data.get("state", ""),
            "url": data.get("url", ""), "comments": comments}


def paragraphs(text: str):
    """按空行切段，保留代码块整体（代码块不参与翻译，作为'不可翻译块'标记）。"""
    out, buf, in_code = [], [], False
    for line in text.split("\n"):
        if line.strip().startswith("```"):
            in_code = not in_code
            buf.append(line)
            if not in_code:
                out.append("\n".join(buf)); buf = []
            continue
        if in_code:
            buf.append(line); continue
        if not line.strip():
            if buf:
                out.append("\n".join(buf)); buf = []
        else:
            buf.append(line)
    if buf:
        out.append("\n".join(buf))
    return [p for p in out if p.strip()]


def flags_of(para: str, glossary: dict) -> list[str]:
    f = []
    modals = []
    for pat, label in MODAL_PATTERNS:
        for m in re.finditer(pat, para):
            modals.append((m.start(), label, m.group(0)))
    if modals:
        modals.sort()
        f.append("义务强度：" + " / ".join(f"{lab}({txt})" for _, lab, txt in modals))
    negs = len(NEGATION.findall(para))
    if negs >= 2:
        f.append(f"否定词 {negs} 处：位置与作用域易被机翻搬动")
    nums = NUMBERS.findall(para)
    if nums:
        f.append("数字/计数：" + "、".join(sorted(set(nums)))[:60] + "（必须逐字核对）")
    spans = CODE_SPAN.findall(para)
    if spans:
        f.append("代码/字段名（必须原样保留）：" + "、".join(spans[:6]))
    refs = SPEC_REF.findall(para)
    if refs:
        f.append("规范引用：" + "、".join(sorted(set(refs)))[:60])
    hinted = sorted({m.group(0).lower() for m in TERM_HINTS.finditer(para)})
    missing = [t for t in hinted if t not in {k.lower() for k in glossary}]
    if missing:
        f.append("未入术语库（译法可能漂移）：" + "、".join(missing[:8]))
    return f


def split_translation(zh_text: str) -> list[str]:
    """把一份译文按空行切段（与原文段落一一对应，段落数不一致时如实报告）。"""
    if not zh_text:
        return []
    return [p.strip() for p in re.split(r"\n\s*\n", zh_text.strip()) if p.strip()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="开源协作的审阅级双语保真工具（不翻译，只保真）")
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--number", required=True, type=int, help="issue 或 PR 编号")
    ap.add_argument("--since", default=None, help="只取此时间之后的评论（ISO，如 2026-10-14）")
    ap.add_argument("--skip-op", action="store_true", help="不翻译 issue/PR 正文，只看评论（配合 --since 用）")
    ap.add_argument("--out", default="oss-translate-out", help="产物目录")
    ap.add_argument("--glossary", default=None, help="术语库 JSON")
    ap.add_argument("--translation", default=None, help="主译文文本（按空行切段，与原文段落对齐）")
    ap.add_argument("--translation2", default=None, help="第二份译文（用于多源比对；分歧会被标出）")
    ap.add_argument("--author", default="", help="审计记录里的操作者（默认取环境变量或 git 用户名）")
    a = ap.parse_args(argv)

    glossary = {}
    gpath = a.glossary or os.path.join(".oss-translate", "glossary.json")
    if os.path.exists(gpath):
        try:
            glossary = json.loads(open(gpath, encoding="utf-8").read())
        except Exception as e:
            print(f"术语库解析失败，忽略：{e}", file=sys.stderr)

    thread = fetch_thread(a.repo, a.number, a.since)
    zh1 = split_translation(open(a.translation, encoding="utf-8").read()) if a.translation else []
    zh2 = split_translation(open(a.translation2, encoding="utf-8").read()) if a.translation2 else []

    os.makedirs(a.out, exist_ok=True)
    lines, terms, risky, idx = [], {}, [], 0
    total_flags = 0

    sections = [("COMMENT", c["body"]) for c in thread["comments"]]
    if not a.skip_op:
        sections = [("OP", thread["body"])] + sections
    for section, text in sections:
        for p in paragraphs(text):
            idx += 1
            tag = f"P{idx:02d}"
            if p.strip().startswith("```"):
                lines.append(f"\n### [{tag}] 代码块（不翻译，原样保留）\n```\n{p.strip().strip('`').strip()}\n```\n")
                continue
            fl = flags_of(p, glossary)
            total_flags += len(fl)
            if fl:
                risky.append((tag, p, fl))
            t1 = zh1[idx - 1] if idx - 1 < len(zh1) else ""
            t2 = zh2[idx - 1] if idx - 1 < len(zh2) else ""
            block = [f"\n### [{tag}]", "", f"**EN（原文）**", "", "> " + p.replace("\n", "\n> "), ""]
            block += [f"**ZH（你的译文）**", "", t1 or "（待填）", ""]
            if a.translation2:
                disagree = (t1.strip() != t2.strip()) if (t1 or t2) else False
                block += [f"**ZH₂（第二份译文）**" + ("  ⚠️ 与主译文不同" if disagree else "（一致）"), "", t2 or "（待填）", ""]
            if fl:
                block += ["**⚠️ 风险标记**"] + [f"- {x}" for x in fl] + [""]
            for m in TERM_HINTS.finditer(p):
                w = m.group(0).lower()
                terms[w] = terms.get(w, 0) + 1
            lines.append("\n".join(block))

    if zh1 and len(zh1) != idx:
        lines.insert(0, f"> ⚠️ 段落数不匹配：原文 {idx} 段，译文 {len(zh1)} 段——逐段核对前请先手工对齐\n")

    open(os.path.join(a.out, "bilingual.md"), "w", encoding="utf-8").write(
        f"# {thread['title']}\n\n{thread['url']} · {thread['state']} · 抽取时间 {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        + "\n".join(lines)
    )

    # 术语表候选
    g = sorted(terms.items(), key=lambda kv: -kv[1])
    rows = ["# 术语表候选", "", "| 术语 | 出现次数 | 入库译法 | 备注 |", "|---|---|---|---|"]
    for w, n in g:
        hit = glossary.get(w) or glossary.get(w.capitalize()) or {}
        rows.append(f"| `{w}` | {n} | {hit.get('zh', '（未入库）')} | {hit.get('note', '')} |")
    open(os.path.join(a.out, "terms.md"), "w", encoding="utf-8").write("\n".join(rows) + "\n")

    # 回帖确认草稿（只引用高风险句）
    conf = ["# 英文确认草稿（发帖前必须先问自己：这几点我真的读对了吗）", "",
            "I want to make sure I have read your points correctly before responding — "
            "could you confirm or correct the following?", ""]
    for tag, p, fl in risky[:8]:
        quote = " ".join(p.split())[:220]
        conf.append(f"- **[{tag}]** You wrote: \"{quote}…\" — my understanding: _(fill in one sentence)_")
        conf.append(f"  - _checks_: {'; '.join(fl)}")
    conf += ["", "If any of the above is a misreading, please say so and I will re-read the thread; "
             "I would rather correct my understanding now than reply on a wrong reading.",
             "", f"— drafted by oss-review-translate for {a.repo}#{a.number}"]
    open(os.path.join(a.out, "confirm.md"), "w", encoding="utf-8").write("\n".join(conf) + "\n")

    who = a.author or os.environ.get("USERNAME") or os.environ.get("USER") or ""
    rec = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tool": "oss-review-translate", "repo": a.repo,
           "number": a.number, "since": a.since, "paragraphs": idx, "flags": total_flags,
           "translations_used": int(bool(a.translation)) + int(bool(a.translation2)),
           "glossary_terms": len(glossary), "by": who}
    with open(os.path.join(a.out, "audit.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"段落 {idx} 个 · 风险标记 {total_flags} 处 · 术语候选 {len(g)} 个 → {a.out}/")
    print("  产物：bilingual.md / terms.md / confirm.md / audit.jsonl")
    return 0


if __name__ == "__main__":
    sys.exit(main())
