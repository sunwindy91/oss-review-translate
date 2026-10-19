# 定位：这一层为什么还空着

> 一页纸说明"已经有什么、缺什么、我们做哪一小块"。写下来是为了被反驳——如果你知道有项目已经做了这件事，
> 请开 issue 指出来，那比一句"不错"有用得多。

## 已经存在的四类东西

| 类别 | 代表 | 服务对象 | 它解决的问题 |
|---|---|---|---|
| **仓库侧自动翻译** | [lizheming/github-translate-action](https://github.com/lizheming/github-translate-action) · [sircharlo/github-translate-action](https://github.com/sircharlo/github-translate-action) · [Mandoa-Labs/MCP-Language-Translator-Issue-Ops](https://github.com/Mandoa-Labs/MCP-Language-Translator-Issue-Ops) | **维护者/社区** | 把非英文 issue 自动译成英文，让更多人能读 |
| **本地化 QA 平台** | [Locadex / General Translation](https://generaltranslation.com/en-US/docs/platform/locadex/reference/automations.mdx) · [LQA agent](https://devpost.com/software/lqa-localization-qa-agent) | **产品字符串** | 翻译质量、术语一致、发布前检查 |
| **机器翻译评测研究** | [WMT 2026](https://www2.statmt.org/wmt26/pdf/2026.wmt-1.51.pdf)（LLM-as-judge、MQM） | **评测者** | 定义"翻译质量"的维度——**术语（terminology）已是 MQM 的标准类别** |
| **商业术语表** | DeepL / Google Translate 的 glossary 功能 | **译者** | 锁定译法，但没有"回帖前确认"这一环 |

## 空着的那一块

上面四类都在回答"**如何把内容翻成另一种语言**"。
没有人回答"**我一个非母语者，怎么确定自己没有读错一条 review，并且敢回帖**"。

具体的缺口（也就是本项目的四个功能）：

1. **义务强度**：`MUST NOT` 被译成"不应"——从禁止降级为建议。翻译工具不会标这个，**评测体系会**（MQM 的 accuracy 维度），但没有工具把它接到"读者"这一端。
2. **否定作用域**：`must not rewrite as refused or open` —— "不得改成二者之一"还是"不得改成 refused，但可以改成 open"？
3. **术语漂移**：同一提案里 `allowance` 出现五种译法，读者以为是五个概念。
4. **确认回路**：读错了没有触发点。**这一条是流程问题，不是翻译问题**——所以本项目把它做成退出码（`--fail-on-high`）而不是提醒。

## 我们刻意不做的事

- **不翻译**：翻译由你（或任何机翻）提供；本项目负责"保真与可核对"。做翻译会和上面四类项目直接竞争，而那不是我判断最缺的东西。
- **不自动回帖**：回帖是公开且不可撤回的。阅读可以自动化，**表态不行**。
- **不做仓库级批量翻译**：那是"让更多人来读"的工具；本项目是"让读的人不出错"的工具。两者可以并存。

## 怎么参与（每个都比点 star 有用）

1. **补一条术语**：往 `.oss-translate/glossary.json` 加一个你踩过坑的词 + 一句 `note`，说明为什么不能按常见译法。
2. **补一类风险**：某个"会改变含义"的语言现象没被标出来 → 开 issue 附最小例句。
3. **给一个反例**：如果你的流程里有个步骤本项目漏了，告诉我们，我们更愿意改流程而不是加功能。
4. **证明我错**：如果你知道已有项目做了同一件事 → 开 issue，我来更新本文档（它会跟着改）。

## 若要登记到 awesome 列表（可直接复制的条目）

```markdown
- [oss-review-translate](https://github.com/sunwindy91/oss-review-translate) — Review-grade
  bilingual fidelity for OSS: paragraph-aligned EN/ZH, glossary lock, obligation-strength and
  negation flags, confirmation draft, reply scaffold, audit line. Not a translator. (Python, MIT)
```
