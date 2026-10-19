# Changelog

## 0.2.1 — 2026-10-20

### Added
- **`--fail-on-high`**：存在 high 级风险时以**退出码 3** 结束（产物照常生成）。
  用途：CI/脚本可以拦下"高风险还没在 `reply.md` 里逐条写下理解"的情况——把"读清楚"变成可执行的约束，
  而不是靠自律。
- **`feishu_card.py`**：把 `summary.json` 变成飞书交互卡片 JSON，并打印一条可粘贴的命令。
  **刻意不自动发送**：群消息是对外不可逆动作（本项目一贯立场：阅读可以自动化，表态不行）。
- **`README.en.md`**：英文版（面向国际读者/潜在协作者）；中文 README 顶部加互链。

### Changed
- 版本 0.2.1（`--version` / `pyproject.toml` 同步）。

### Verified
- `tests/test_flags.py` → OK；`tests/test_all.py` → ALL_OK（新增 5 条断言：fail-on-high 返回 3、带 artifacts、
  无 high 时返回 0、卡片为 interactive、卡片含高风险段落编号）。

## 0.2.0 — 2026-10-19

从第一性原理重做输出：**交付物不是"译文"，而是"一条你愿意发出去的回复"**。

### Changed（信号不再被稀释）
- **风险标记分级** `high / medium / low`，**默认只显示 high**（`--all-flags` 看全部）。
  实测：9 段规范文本原本会产出 28 条标记 —— 那等于没有标记。
  分级规则：
  - **high**：`MUST / MUST NOT / SHALL / SHALL NOT`（强制/禁止语气，**不可降级为"应当/可以"**）；否定词 ≥2（作用域易被搬动）；有强制语气时的数字计数
  - **medium**：`should / may / can`；数字与计数；代码字段与 § 引用；未入术语库的术语
  - **low**：单个否定等
- `bilingual.md` 顶部新增**一行汇总**：`段落 N · 高风险 X · 中 Y · 低 Z`

### Added
- **`reply.md`（回复脚手架）**：把"读"接到"写"——高风险段落先写「我的理解 / 需要对方确认」，再逐段回应，最后附"回帖前自查"清单（每条都能指回段落编号）。
- **`--format json`**：产出 `summary.json`（段落 + 分级标记），供飞书卡片/自动化接入。
- **`--version`**；版本号进 `pyproject.toml`（可 `pip install .`）。

### Fixed
- 确认稿只引用 **high** 级段落，并改用 `must verify:` 前缀（避免把中低风险也堆给对方）。

## 0.1.0 — 2026-10-17

首个可用版本：双语逐段对齐、术语库锁定、风险标记、英文确认稿、审计行；
`--from-json/--save-json`（离线与可复现）、`--exclude-author`、隐私（审计不写本机用户名）、
端到端离线测试与 GitHub CI。
