# 零依赖单测：只用标准库（不做网络调用）
#   python tests/test_flags.py   → 期望输出 OK
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import importlib.util

spec = importlib.util.spec_from_file_location(
    "ort", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "oss-review-translate.py"))
ort = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ort)

GLOSSARY = {"allowance": {"zh": "额度"}, "dispatch": {"zh": "派发"}}


def joined(para):
    return " ".join(ort.flags_of(para, GLOSSARY))


cases = [
    # 义务强度必须被标出（机翻最容易把它拉平）
    ("The host MUST NOT restore the allowance.", ["义务强度", "MUST NOT"]),
    ("The host should reconcile the original attempt.", ["should"]),
    # 否定词 ≥2 要提示作用域风险
    ("Do not rewrite the decision as refused or open, and do not invent a timestamp.", ["否定词"]),
    # 数字/计数
    ("There must be exactly one dispatch and zero additional effects.", ["数字"]),
    # 代码字段必须原样保留
    ("Fields `validUntil` and `effectNotBefore` are set.", ["validUntil", "effectNotBefore"]),
    # 规范引用
    ("See §10 for the emergency path.", ["§10"]),
    # 未入库术语
    ("The steward records the sanction.", ["未入术语库", "sanction", "steward"]),
]

fails = 0
for para, wants in cases:
    got = joined(para)
    for w in wants:
        if w not in got:
            print(f"  ✗ 缺少标记 {w!r} ← {para[:60]}")
            fails += 1
# 已入库的术语不得被列为"未入术语库"
got_g = joined("The allowance is spent on one dispatch.")
if "未入术语库" in got_g and ("allowance" in got_g or "dispatch" in got_g):
    print("  ✗ 已入库术语被误报为未入库:", got_g)
    fails += 1

# 反例：普通叙述不应产生"义务强度"标记
if "义务强度" in joined("Thanks for the review, this is helpful."):
    print("  ✗ 普通叙述被误标为义务强度")
    fails += 1
# 段落切分：代码块必须整体保留
paras = ort.paragraphs("A\n\n```py\nx=1\n```\n\nB")
if len(paras) != 3 or not paras[1].startswith("```"):
    print("  ✗ 代码块切分不符预期:", paras)
    fails += 1

print("OK" if fails == 0 else f"FAIL({fails})")
sys.exit(0 if fails == 0 else 1)
