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


def fetch_thread_raw(repo: str, number: int) -> dict:
    """拉原始线程（gh --json 形态，不做过滤）。"""
    j = subprocess.run(
        ["gh", "issue", "view", str(number), "-R", repo, "--json", "title,body,state,url,comments"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if j.returncode != 0:
        j = subprocess.run(
            ["gh", "pr", "view", str(number), "-R", repo, "--json", "title,body,state,url,comments"],
            capture_output=True, text=True, encoding="utf-8",
        )
    if j.returncode != 0:
        raise SystemExit("gh 拉取失败：" + (j.stderr or j.stdout)[:300])
    return json.loads(j.stdout)


def normalize_thread(data: dict, since: str | None = None, exclude: str | None = None) -> dict:
    """把线程规整成统一形态并做过滤（兼容 gh 形态与更宽松的扁平形态）。"""
    comments = []
    for c in data.get("comments", []):
        author = c.get("author")
        login = author.get("login", "?") if isinstance(author, dict) else (author or "?")
        ts = c.get("createdAt") or c.get("created_at") or ""
        if since and ts and ts < since:
            continue
        if exclude and login == exclude:
            continue
        comments.append({"author": login, "at": ts, "body": c.get("body") or ""})
    return {"title": data.get("title", ""), "body": data.get("body") or "",
            "state": data.get("state", ""), "url": data.get("url", ""), "comments": comments}


def fetch_thread(repo: str, number: int, since: str | None, exclude: str | None = None) -> dict:
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
        if exclude and (c.get("author") or {}).get("login") == exclude:
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


VERSION = "0.2.2"


def flags_of(para: str, glossary: dict):
    """返回 [(level, text)]，level ∈ high / medium / low。

    分级的意义（第一性原理）：**只有会改变含义的标记才值得占用注意力**。
    实测：9 段规范文本原样会产出 28 条标记 —— 那等于没有标记。
      high   强制/禁止语气（MUST / MUST NOT / SHALL / SHALL NOT）；否定 ≥2 处
      medium 建议/允许语气（should / may / can）；数字与计数；代码字段与 §引用；未入术语库
      low    单个否定；其他
    """
    out = []
    strong = []
    for pat, label in MODAL_PATTERNS:
        for m in re.finditer(pat, para):
            strong.append((m.start(), label, m.group(0)))
    strong.sort()
    musts = [(lab, txt) for _, lab, txt in strong if lab.startswith("强制") or lab.startswith("禁止")]
    softs = [(lab, txt) for _, lab, txt in strong if not (lab.startswith("强制") or lab.startswith("禁止"))]
    if musts:
        out.append(("high", "强制/禁止语气：" + " / ".join(f"{lab}({txt})" for lab, txt in musts)
                    + " —— 中文必须对应为 必须/不得，不可降级为『应当/可以』"))
    if softs:
        out.append(("medium", "建议/允许语气：" + " / ".join(f"{lab}({txt})" for lab, txt in softs)))
    negs = len(NEGATION.findall(para))
    if negs >= 2:
        out.append(("high", f"否定词 {negs} 处 —— 作用域易被机翻搬动（not A and B ≠ not (A and B)）"))
    elif negs == 1:
        out.append(("low", "否定词 1 处"))
    nums = NUMBERS.findall(para)
    if nums:
        lvl = "high" if musts else "medium"
        out.append((lvl, "数字/计数：" + "、".join(sorted(set(nums)))[:60] + "（逐字核对）"))
    spans = CODE_SPAN.findall(para)
    if spans:
        out.append(("medium", "代码/字段名（原样保留）：" + "、".join(spans[:6])))
    refs = SPEC_REF.findall(para)
    if refs:
        out.append(("medium", "规范引用：" + "、".join(sorted(set(refs)))[:60]))
    hinted = sorted({m.group(0).lower() for m in TERM_HINTS.finditer(para)})
    missing = [t for t in hinted if t not in {k.lower() for k in glossary}]
    if missing:
        out.append(("medium", "未入术语库（译法可能漂移）：" + "、".join(missing[:8])))
    return out


def split_translation(zh_text: str) -> list[str]:
    """把一份译文按空行切段（与原文段落一一对应，段落数不一致时如实报告）。"""
    if not zh_text:
        return []
    return [p.strip() for p in re.split(r"\n\s*\n", zh_text.strip()) if p.strip()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="开源协作的审阅级双语保真工具（不翻译，只保真）")
    ap.add_argument("--repo", default="", help="owner/name（用 --from-json 时可省略）")
    ap.add_argument("--number", default=0, type=int, help="issue 或 PR 编号（用 --from-json 时可省略）")
    ap.add_argument("--from-json", default=None, help="从本地 JSON 读取线程（离线/存档/可复现）")
    ap.add_argument("--all-flags", action="store_true", help="显示全部风险（默认只显示 high 级）")
    ap.add_argument("--format", default="md", choices=["md", "json"], help="md（默认）或 json（给自动化/飞书用）")
    ap.add_argument("--version", action="version", version="oss-review-translate " + VERSION)
    ap.add_argument("--fail-on-high", action="store_true",
                    help="存在 high 级风险时以退出码 3 结束（供 CI/脚本拦下『高风险尚未确认』）")
    ap.add_argument("--save-json", default=None, help="把读到的线程原样存为 JSON（审计可复现）")
    ap.add_argument("--since", default=None, help="只取此时间之后的评论（ISO，如 2026-10-14）")
    ap.add_argument("--skip-op", action="store_true", help="不翻译 issue/PR 正文，只看评论（配合 --since 用）")
    ap.add_argument("--exclude-author", default=None, help="跳过某个作者的评论（如你自己的账号），避免把自己的回帖算进\"新回复\"")
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

    if a.from_json:
        raw = json.loads(open(a.from_json, encoding="utf-8").read())
    else:
        if not a.repo or not a.number:
            raise SystemExit("需要 --repo 与 --number（或用 --from-json）")
        raw = fetch_thread_raw(a.repo, a.number)
        if a.save_json:
            with open(a.save_json, "w", encoding="utf-8") as fh:
                json.dump(raw, fh, ensure_ascii=False, indent=2)
    thread = normalize_thread(raw, a.since, a.exclude_author)
    if not a.repo and thread.get("url"):
        # 从 URL 反推 owner/name#number，让 --from-json 也能产出完整审计
        m = re.search(r"github\.com/([^/]+/[^/]+)/(?:issues|pull)/(\d+)", thread["url"])
        if m:
            a.repo, a.number = m.group(1), int(m.group(2))
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
            shown = fl if a.all_flags else [f for f in fl if f[0] == "high"]
            if fl:
                risky.append((tag, p, fl))
            t1 = zh1[idx - 1] if idx - 1 < len(zh1) else ""
            t2 = zh2[idx - 1] if idx - 1 < len(zh2) else ""
            block = [f"\n### [{tag}]", "", f"**EN（原文）**", "", "> " + p.replace("\n", "\n> "), ""]
            block += [f"**ZH（你的译文）**", "", t1 or "（待填）", ""]
            if a.translation2:
                disagree = (t1.strip() != t2.strip()) if (t1 or t2) else False
                block += [f"**ZH₂（第二份译文）**" + ("  ⚠️ 与主译文不同" if disagree else "（一致）"), "", t2 or "（待填）", ""]
            if shown:
                block += ["**⚠️ 风险标记**"] + [f"- [{lvl}] {txt}" for lvl, txt in shown] + [""]
                hidden = len(fl) - len(shown)
                if hidden:
                    block += [f"*（另有 {hidden} 条中/低风险，--all-flags 查看）*", ""]
            elif fl and a.all_flags is False:
                block += [f"*（{len(fl)} 条中/低风险已隐藏，--all-flags 查看）*", ""]
            for m in TERM_HINTS.finditer(p):
                w = m.group(0).lower()
                terms[w] = terms.get(w, 0) + 1
            lines.append("\n".join(block))

    high_n = sum(1 for _, _, fl in risky for lvl, _ in fl if lvl == "high")
    mid_n = sum(1 for _, _, fl in risky for lvl, _ in fl if lvl == "medium")
    low_n = sum(1 for _, _, fl in risky for lvl, _ in fl if lvl == "low")
    head = (f"# {thread['title']}\n\n{thread['url']} · {thread['state']} · 抽取 "
            f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n"
            f"> 段落 {idx} · **高风险 {high_n}** · 中 {mid_n} · 低 {low_n}"
            + ("　（默认只显示高风险，`--all-flags` 看全部）" if not a.all_flags else "") + "\n")
    if zh1 and len(zh1) != idx:
        lines.insert(0, f"> ⚠️ 段落数不匹配：原文 {idx} 段，译文 {len(zh1)} 段——逐段核对前请先手工对齐\n")

    open(os.path.join(a.out, "bilingual.md"), "w", encoding="utf-8").write(head + "\n".join(lines))

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
        checks = [txt for lvl, txt in fl if lvl == "high"]
        if checks:
            conf.append(f"  - _must verify_: {'; '.join(checks)}")
    conf += ["", "If any of the above is a misreading, please say so and I will re-read the thread; "
             "I would rather correct my understanding now than reply on a wrong reading.",
             "", f"— drafted by oss-review-translate for {a.repo}#{a.number}"]
    open(os.path.join(a.out, "confirm.md"), "w", encoding="utf-8").write("\n".join(conf) + "\n")

    # 隐私：默认**不**写本机用户名（它是可识别信息）；需要追责就显式 --author
    # 回复脚手架：把"读"接到"写"——带段落锚点，避免凭印象回帖
    reply = ["# 回复脚手架（先确认，再回复；每条都带段落编号可回指）", "",
             "## 一、需要先向对方确认的点（高风险）", ""]
    for tag, p, fl in risky:
        if any(lvl == "high" for lvl, _ in fl):
            reply.append(f"- [{tag}] 我的理解：____　需要对方确认：____")
    reply += ["", "## 二、逐段回应", ""]
    for tag, p, fl in risky:
        first = " ".join(p.split())[:90]
        reply.append(f"- [{tag}]（原文：{first}…）→ 我的回应：____")
    reply += ["", "## 三、回帖前自查", "- [ ] 每个高风险段落都写了『我的理解』",
              "- [ ] 术语译法与术语库一致", "- [ ] 没有一句是只凭译文写的（都能指回段落编号）"]
    open(os.path.join(a.out, "reply.md"), "w", encoding="utf-8").write("\n".join(reply) + "\n")

    if a.format == "json":
        payload = {"tool": "oss-review-translate", "version": VERSION, "repo": a.repo, "number": a.number,
                   "url": thread["url"], "title": thread["title"],
                   # 总量与"有风险的段落"是两个数：下游（卡片/看板）必须能分开显示
                   "total_paragraphs": idx,
                   "paragraphs": [
                       {"tag": tag, "en": p, "flags": [{"level": l, "text": t} for l, t in fl]}
                       for tag, p, fl in risky],
                   "counts": {"high": high_n, "medium": mid_n, "low": low_n}}
        with open(os.path.join(a.out, "summary.json"), "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)

    who = a.author or ""
    rec = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tool": "oss-review-translate", "repo": a.repo,
           "number": a.number, "since": a.since, "paragraphs": idx, "flags": total_flags,
           "translations_used": int(bool(a.translation)) + int(bool(a.translation2)),
           "glossary_terms": len(glossary), "by": who or "unspecified"}
    with open(os.path.join(a.out, "audit.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"段落 {idx} 个 · 风险 high {high_n} / mid {mid_n} / low {low_n} · 术语候选 {len(g)} 个 → {a.out}/")
    if a.fail_on_high and high_n > 0:
        print(f"  --fail-on-high：存在 {high_n} 条高风险，退出码 3（请先在 reply.md 里逐条写下你的理解再回帖）")
        return 3
    print("  产物：bilingual.md / terms.md / confirm.md / reply.md / audit.jsonl"
          + (" / summary.json" if a.format == "json" else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
