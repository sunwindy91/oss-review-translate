# -*- coding: utf-8 -*-
"""端到端测试：完全离线（用 --from-json 的回放能力），不依赖网络与 gh。

    python tests/test_all.py     → 期望输出 ALL_OK

覆盖：段落切分/过滤(--since,--exclude-author)/翻译对齐/术语库/风险标记/
      确认稿/审计字段/隐私(不写用户名)/双译比对/错误路径
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "oss-review-translate.py")
GLOSSARY = os.path.join(ROOT, ".oss-translate", "glossary.json")
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("  ✗ " + msg)


def run(args, cwd):
    return subprocess.run([sys.executable, TOOL] + args, cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def read(path):
    return io_open(path)


def io_open(path):
    import io as _io
    return _io.open(path, encoding="utf-8").read()


FIXTURE = {
    "title": "Fixture: normative text with traps",
    "state": "OPEN",
    "url": "https://github.com/example/repo/issues/42",
    "body": "OP body with a MUST and `code`.\n\n```py\nx = 1\n```\n",
    "comments": [
        {"author": {"login": "alice"}, "createdAt": "2026-10-01T00:00:00Z",
         "body": "OLDCOMMENT should be filtered out by --since."},
        {"author": {"login": "bob"}, "createdAt": "2026-10-15T00:00:00Z",
         "body": "The host MUST NOT restore the allowance.\n\n"
                 "Do not rewrite the decision as refused or open, and do not invent a timestamp.\n\n"
                 "There must be exactly one dispatch and zero additional effects.\n\n"
                 "Fields `validUntil` and `effectNotBefore` are set; see §10.\n\n"
                 "Reconciliation of the original attempt is required before any new decision."},
        {"author": {"login": "me"}, "createdAt": "2026-10-16T00:00:00Z",
         "body": "MYOWNREPLY should be filtered out by --exclude-author."},
    ],
}

ZH = ("主机**不得**恢复额度。\n\n"
      "不要把决定改写成 refused 或 open，也不要凭空造一个时间戳。\n\n"
      "必须**恰好一次派发**，且**零**额外效果。\n\n"
      "字段 `validUntil` 与 `effectNotBefore` 会被设置；见 §10。\n\n在任何新决定之前，必须先对原始尝试做对账。\n")


def main():
    tmp = tempfile.mkdtemp(prefix="ort-test-")
    try:
        fx = os.path.join(tmp, "thread.json")
        with open(fx, "w", encoding="utf-8") as fh:
            json.dump(FIXTURE, fh, ensure_ascii=False)
        zh = os.path.join(tmp, "zh.txt")
        with open(zh, "w", encoding="utf-8") as fh:
            fh.write(ZH)
        out = os.path.join(tmp, "out")

        base = ["--from-json", fx, "--since", "2026-10-14", "--skip-op",
                "--exclude-author", "me", "--glossary", GLOSSARY, "--out", out]
        r = run(base + ["--translation", zh], tmp)
        check(r.returncode == 0, "基本运行应成功，实际退出码 %d：%s" % (r.returncode, (r.stderr or "")[:200]))
        for f in ("bilingual.md", "terms.md", "confirm.md", "audit.jsonl"):
            check(os.path.exists(os.path.join(out, f)), "缺少产物 " + f)

        bi = read(os.path.join(out, "bilingual.md"))
        check("MUST NOT" in bi and "不得" in bi, "双语对照应同时含原文与译文")
        check("OLDCOMMENT" not in bi, "--since 应过滤掉旧评论")
        check("MYOWNREPLY" not in bi, "--exclude-author 应过滤掉自己的评论")
        check("（待填）" not in bi, "译文应与原文段落对齐（不应出现待填）")
        check(bi.count("### [P") == 5, "段落数应为 5，实际 %d" % bi.count("### [P"))
        check("风险标记" in bi, "应标记风险")

        terms = read(os.path.join(out, "terms.md"))
        check("`dispatch`" in terms and "派发" in terms, "术语表应命中 glossary 的 dispatch→派发")
        check("reconciliation" in terms and "（未入库）" in terms, "术语表应列出未入库术语（reconciliation）")

        conf = read(os.path.join(out, "confirm.md"))
        check("Did I understand" in conf or "I want to make sure" in conf, "确认稿应含确认问句")
        check(conf.count("You wrote:") >= 2, "确认稿应引用多条高风险原文")

        rec = json.loads(read(os.path.join(out, "audit.jsonl")).strip().splitlines()[-1])
        check(rec["paragraphs"] == 5, "审计的 paragraphs 应为 5")
        check(rec["translations_used"] == 1, "审计的 translations_used 应为 1")
        check(rec["glossary_terms"] > 0, "审计的 glossary_terms 应 > 0")
        check(rec["by"] == "unspecified", "审计默认不得写本机用户名（隐私）")
        check(rec["repo"] == "example/repo" and rec["number"] == 42, "应从 URL 反推 repo/number")

        # 隐私：任何产物都不得出现本机用户名
        user = os.environ.get("USERNAME") or os.environ.get("USER") or ""
        if user:
            for f in ("bilingual.md", "terms.md", "confirm.md", "audit.jsonl"):
                check(user not in read(os.path.join(out, f)), "产物 %s 泄露本机用户名" % f)

        # 双译比对
        zh2 = os.path.join(tmp, "zh2.txt")
        with open(zh2, "w", encoding="utf-8") as fh:
            fh.write("主机应当恢复额度。\n\n" + "\n\n".join(ZH.split("\n\n")[1:]))
        out2 = os.path.join(tmp, "out2")
        r2 = run(base[:-1] + [out2, "--translation", zh, "--translation2", zh2], tmp)
        check(r2.returncode == 0, "双译运行应成功")
        bi2 = read(os.path.join(out2, "bilingual.md"))
        check("⚠️ 与主译文不同" in bi2, "双译应标出分歧")
        check("（一致）" in bi2, "双译应标出相同的段落")

        # 不带 --since 时应包含旧评论
        out3 = os.path.join(tmp, "out3")
        r3 = run(["--from-json", fx, "--skip-op", "--exclude-author", "me",
                  "--glossary", GLOSSARY, "--out", out3], tmp)
        check(r3.returncode == 0, "不带 since 应成功")
        check("OLDCOMMENT" in read(os.path.join(out3, "bilingual.md")), "不带 since 时应保留旧评论")

        # 错误路径
        bad = run(["--from-json", os.path.join(tmp, "nope.json"), "--out", out], tmp)
        check(bad.returncode != 0, "缺失 --from-json 文件时应非零退出")
        noargs = run(["--skip-op"], tmp)
        check(noargs.returncode != 0, "既无 repo/number 也无 from-json 时应非零退出")

        # ---- v0.2.1：--fail-on-high 与飞书卡片 ----
        fx2 = os.path.join(tmp, "high.json")
        with open(fx2, "w", encoding="utf-8") as fh:
            json.dump({"title": "T", "body": "", "state": "OPEN", "url": "https://github.com/a/b/issues/9",
                       "comments": [{"author": {"login": "bob"}, "createdAt": "2026-10-15T00:00:00Z",
                                     "body": "The host MUST NOT restore it."}]}, fh)
        out4 = os.path.join(tmp, "out4")
        r4 = run(["--from-json", fx2, "--skip-op", "--out", out4, "--fail-on-high"], tmp)
        check(r4.returncode == 3, "--fail-on-high 应返回 3，实际 %d" % r4.returncode)
        check(os.path.exists(os.path.join(out4, "bilingual.md")), "返回 3 时产物仍应生成")

        out5 = os.path.join(tmp, "out5")
        r5 = run(["--from-json", fx2, "--skip-op", "--out", out5, "--fail-on-high", "--all-flags"], tmp)
        check(r5.returncode == 3, "带 --all-flags 时仍应返回 3")

        # 卡片：只用 summary.json 生成，不发送
        summary_path = os.path.join(tmp, "s.json")
        with open(summary_path, "w", encoding="utf-8") as fh:
            json.dump({"repo": "a/b", "number": 3, "title": "T", "url": "https://x/y",
                       "counts": {"high": 1, "medium": 0, "low": 0},
                       "paragraphs": [{"tag": "P01", "en": "x", "flags": [{"level": "high", "text": "MUST NOT"}]}]}, fh)
        card_path = os.path.join(tmp, "card.json")
        rc = subprocess.run([sys.executable, os.path.join(ROOT, "feishu_card.py"), summary_path, "--out", card_path],
                            capture_output=True, text=True, encoding="utf-8")
        check(rc.returncode == 0, "feishu_card 应成功：" + (rc.stderr or "")[:150])
        card = json.loads(io_open(card_path))
        check(card["msg_type"] == "interactive", "卡片应为 interactive")
        check("P01" in json.dumps(card, ensure_ascii=False), "卡片应含高风险段落编号")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        print("FAIL(%d)" % len(fails))
        return 1
    print("ALL_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
