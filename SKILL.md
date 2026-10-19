---
name: oss-review-translate
description: Use when reading or replying to English GitHub issues/PR reviews in a non-native language and translation fidelity matters: normative words (MUST/should/may), negation, counts, code identifiers, or terminology drift (sanction/allowance/dispatch/effect). Produces a paragraph-aligned bilingual file, a glossary check, risk flags, an English confirmation draft, and an audit line. Triggers: 英文review、翻译、双语、术语、máquina、机翻不准、语义、回到原文、confirm understanding、glossary、allowance、sanction、must/should、歧义
---

# oss-review-translate

**何时看**：你要读/回一条英文 issue 或 PR review，并且**读错的代价高**（规范文本、协议提案、招标/授权语义）。
典型信号：机翻把 `MUST` 与 `should` 译成同一个词；`allowance`/`sanction`/`dispatch`/`effect` 在不同段落译法不一致；
你不确定 `hold off` 是"拒绝"还是"暂缓"；你想在回帖前先让对方确认。

**不要用它**：日常闲聊式评论、纯代码 review（没有语义歧义）、你不打算回复的任何内容。

## 步骤

1. 抽取新评论（只取新回复，不重读整帖）：
   ```bash
   python oss-review-translate.py --repo owner/name --number 123 --since YYYY-MM-DD --skip-op --out out/
   ```
2. 把已有译文的**每一段按空行分段**贴进 `zh.txt`，加 `--translation zh.txt` 重跑；
   若还有第二份译文，加 `--translation2 zh2.txt`，工具会标出**逐段分歧**。
3. 逐段读 `out/bilingual.md`：**先读原文，再读译文**；对每个"⚠️ 风险标记"做判断：
   - 义务强度：must / must not / should / may —— 该段是**要求**还是**建议**还是**允许**？
   - 否定：数一遍否定词，确认作用域（"not A and B" ≠ "not (A and B)"）
   - 数字：`one dispatch`、`zero effects`、`exactly once` —— 逐个核对
   - 未入库术语：从 `out/terms.md` 补进 `.oss-translate/glossary.json`
4. 用 `out/confirm.md` 起草"我理解对了吗"的英文确认；**确认后再**写实质回复。
5. 回帖前检查 `out/audit.jsonl` 是否落下了一行（用于事后回答"你依据什么理解的"）。

## 判据（做到什么算完成）

1. **先跑 `--fail-on-high`**：退出码 **3** 表示还有 high 级段落没写下你的理解 → **不许回帖**，
   先到 `out/reply.md` 里逐条写「我的理解是…」。这是**可执行**的约束，不是提醒。
2. 每个高风险段落**都有**你写下的一句"我的理解是…"
3. 术语表里**没有**新出现的未入库技术名词（或你明确决定不锁定它）
4. 回帖内容里**没有**任何一句是"只凭译文写的"（必须能指回原文段落编号 `[P12]`）
5. 回帖前**先发确认**（用 `confirm.md`），对方确认后再写实质回复

> 为什么把它写成"判据"而不是"建议"：被误读过的人都懂——**问题不是不知道该核对，而是核对没有触发点**。
> 退出码就是触发点：红了就不能发。

## 失败形态（本技能存在的理由）

- **义务强度被拉平**：规范里 `MUST NOT restore the allowance` 被译成"不应恢复额度"→ 强度从"禁止"降为"建议"，
  于是你以为对方只是"倾向"。→ 这类段落**必须回原文**。
- **术语漂移**：同一提案里 `allowance` 被译成"配额/额度/许可"三种，读者以为是三件事。
- **否定作用域**：`must not rewrite the decision as refused or open` 是"不得改写成二者之一"，
  而不是"不得改写成 refused，但可以改写成 open"。
- **礼貌语误读**：`hold off` = 暂缓；`I would be glad to` = 愿意；`not validated` = 尚未验证（不是"无效"）。

## 相关

- `dsh-tool-meta`：对外动作闸门与审计账本（回帖前先声明你核验了什么）。
- 术语库样例：`.oss-translate/glossary.json`（A2A Sanction Gate 提案的 21 个高频术语）。
