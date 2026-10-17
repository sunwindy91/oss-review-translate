# 快速上手（3 分钟）

> 这是一个**单文件脚本**，不是服务、不需要装依赖。它**不翻译**——它保证你"读得准、能核对、可回帖确认"。

## 0. 前提

- Python 3.9+
- [`gh` CLI](https://cli.github.com/) 且已登录：`gh auth login`（脚本用它拉 issue/PR 评论）

## 1. 最常用的一条命令

```bash
git clone https://github.com/sunwindy91/oss-review-translate.git
cd oss-review-translate

# 只看 10-14 之后的新评论，生成双语骨架 + 术语表 + 确认稿 + 审计行
python oss-review-translate.py --repo a2aproject/A2A --number 2250 \
    --since 2026-10-14 --skip-op --out out/
```

产物在 `out/`：

| 文件 | 用途 |
|---|---|
| `bilingual.md` | **原文↔译文逐段对照**，每段 `[P07]` 编号，带 ⚠️ 风险标记 |
| `terms.md` | 术语候选 + 你的术语库命中情况（未入库的会标出来） |
| `confirm.md` | **英文确认稿**：只引用高风险原句，问"我这样理解对吗" |
| `audit.jsonl` | 一行审计：哪版、几段、多少风险、用了几份译文 |

## 2. 你已经有机翻译文（比如 QQ 邮箱翻译）

把译文**按空行分段**贴进 `zh.txt`（段数与原文一致），然后：

```bash
python oss-review-translate.py --repo a2aproject/A2A --number 2250 \
    --since 2026-10-14 --skip-op --translation zh.txt --out out/
```

若你还有第二份译文（另一家），再加 `--translation2 zh2.txt` → 工具会**逐段标出两份译文的分歧**。
段落数对不上时，`bilingual.md` 顶部会明确警告。

## 3. 最短闭环（30 秒）

1. 跑第 1 步
2. 打开 `out/bilingual.md`，**只看带 ⚠️ 的段落**
3. 每段回原文核对四件事：**义务强度**（must/must not/should/may）、**否定作用域**、**数字/计数**、**代码字段与 §引用**
4. 用 `out/confirm.md` 起草"我理解对了吗"，**确认后再**发实质回复

## 4. 术语库（最有复用价值的部分）

默认读 `./.oss-translate/glossary.json`（仓库里已带 21 条 A2A Sanction Gate 提案的高频术语）：

```json
{
  "allowance": { "zh": "额度（可用的次数预算）", "note": "single-use allowance = 单次额度；与 validUntil（时间窗）是两个维度" }
}
```

**规则**：只锁定"会引发分歧"的词；每条必须有 `note` 说明为什么不能按常见译法。

## 5. 它刻意不做的事

- **不翻译**：译文由你或机翻提供（它负责保真与可核对）
- **不自动回帖**：回帖是不可逆的对外动作，误读会被直接发布出去。它只给你证据和确认稿

## 6. 自检

```bash
python tests/test_flags.py     # 期望输出 OK（零依赖，不联网）
```
