# oss-review-translate · 审阅级双语保真

[![test](https://github.com/sunwindy91/oss-review-translate/actions/workflows/test.yml/badge.svg)](https://github.com/sunwindy91/oss-review-translate/actions/workflows/test.yml)

> 面向"**非母语者在开源协作里读英文 review**"的工具。**它不是翻译器**——它保证的是
> **读得准、能核对、可回帖确认、留得下审计**。

## 它解决什么（一句话）

机翻的失效点不在"词"，而在四件事：**对齐、术语、义务强度、确认环节**。
这个工具把四件事变成确定性、可复现、可审计的动作，**不依赖任何模型**。

| 失效点 | 现实后果 | 本工具的做法 |
|---|---|---|
| **对齐** | 整段译完无法逐句核对，错在第三句你看不出来 | 原文↔译文**逐段并排**，每段有 `[P12]` 编号可回指 |
| **术语** | `allowance` 在五段里有四种译法；`sanction` 被译成"制裁" | **术语库**锁定译法；未入库的技术名词**列出候选**（`terms.md`） |
| **义务强度** | `MUST` / `should` / `may` 被拉平成"应该"或"可以" | 逐段标出**义务强度**，并标否定词数量、数字/计数、代码字段、规范引用 |
| **确认环节** | 读错直接进你的英文回复，对方再纠正一轮 | 生成 **英文确认草稿**（"Did I understand correctly…"），只引用高风险句 |
| 多源校验 | 单一机翻没有交叉验证 | `--translation2` 提供第二份译文，**逐段比对并标出分歧** |
| 审计 | 事后无法回答"你当时依据什么理解的" | `audit.jsonl` 一行记录：哪版、几段、多少风险、用了几份译文 |

## 用法

```bash
# 只看 10-14 之后的新评论，并生成双语骨架/术语/确认稿
python oss-review-translate.py --repo a2aproject/A2A --number 2250 \
    --since 2026-10-14 --skip-op --out out/

# 你已有两份译文（QQ 邮箱机翻 + 另一家）：逐段比对，标出分歧句
python oss-review-translate.py --repo a2aproject/A2A --number 2250 \
    --since 2026-10-14 --skip-op --translation zh.txt --translation2 zh2.txt --out out/

# 指定术语库（默认读 ./.oss-translate/glossary.json）
python oss-review-translate.py ... --glossary path/to/glossary.json
```

产物：`bilingual.md`（逐段对照 + 风险标记）· `terms.md`（术语候选）· `confirm.md`（英文确认草稿）· `audit.jsonl`

## 推荐的协作流程（四步，缺一不可）

1. **抽取**：`--since` + `--skip-op` 只拉新评论，避免重读整帖
2. **对齐**：把机翻结果按空行分段贴进 `zh.txt` → 逐段核对（工具会报告段落数不匹配）
3. **校验**：高风险段落（义务强度/否定/数字/未入库术语）**逐条回原文确认**；有第二份译文就比对
4. **回帖**：用 `confirm.md` 先问"我理解对了吗"，**再**写实质回复；把审计行留在 `audit.jsonl`


## 离线与复现（`--save-json` / `--from-json`）

```bash
# 把"你当时读到的线程"存档 → 审计可复现（对方事后编辑/删除也能对照）
python oss-review-translate.py --repo a2aproject/A2A --number 2250 --save-json thread.json --out out/

# 之后可离线重跑同一份快照（同一输入 → 同一输出），不依赖网络
python oss-review-translate.py --from-json thread.json --since 2026-10-14 --skip-op --out out2/
```

## 测试

```bash
python tests/test_flags.py   # 风险标记的单元断言（零依赖）
python tests/test_all.py     # 端到端、离线回放（不联网、不需要 gh）
```

CI：`.github/workflows/test.yml`（push / PR 时自动跑上面两个）。

## 诚实边界

- **它不翻译**。译文由你（或任何机翻）提供；工具负责"保真与可核对"。
- 风险检测是**启发式**（按英文规范文本调校），会有漏检；发现漏检请提 issue。
- `MUST`/`should` 的标注是**提示**，不替你做语义判断——它只是让"你正在做这个判断"这件事可见。
- 段落切分按空行；原文用特殊排版（表格内多段、无空行长段）时可能对不齐，工具会报告段落数不匹配。

## 为什么不做成"自动翻译 + 自动回帖"

因为在开源协作里，**回帖是不可逆的对外动作**。把"翻译→判断→回帖"自动化，等于把误解直接发布出去。
这个工具刻意停在"**给你证据 + 让你确认**"这一步。

## 与 dsh-tool-meta 的关系

同源的设计原则：**先声明后执行**（回帖前先产出 `confirm.md`）、**留痕**（`audit.jsonl`）、
**不确定就标出来而不是猜**（风险标记）。若在装有 `dsh-tool-meta` 的环境里回帖，
那条"对外动作闸门"会要求你先声明自己核验了什么——与本工具的第 4 步天然衔接。

## License

MIT（与 dsh-tool-meta 一致）。欢迎提 issue 补充术语库与失败案例。
