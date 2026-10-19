# 术语表候选

| 术语 | 出现次数 | 入库译法 | 备注 |
|---|---|---|---|
| `sanction` | 10 | 批准（人类对不可逆动作的授权） | 本提案里指'具名人管家对某一次不可逆动作的批准'，不是'制裁'。机翻常误译为'制裁' |
| `dispatch` | 7 | 派发 | 与 effect（效果）区分：派发=送出请求，效果=下游真的发生了 |
| `allowance` | 7 | 额度（可用的次数预算） | single-use allowance = 单次额度；与 validUntil（时间窗）是两个维度 |
| `outcome` | 5 | 结局／结果状态 | 词表：pending / refused / lapsed / open —— 刻意与 A2A 核心任务状态区分 |
| `binding` | 4 | 约束性规范文本 | 本提案把自己叫 binding（有约束力的那部分），与 commentary 区分 |
| `recovery` | 4 | （未入库） |  |
| `admission` | 3 | 受理 | dispatch admission = 派发受理时点；关键在'受理即占额' |
| `effect` | 3 | 效果（下游实际发生的结果） | effect confirmed / unknown 是观测状态，不是批准状态 |
| `claim` | 3 | （未入库） |  |
| `spent` | 2 | （未入库） |  |
| `conformance` | 2 | 一致性（是否符合规范） | conformance test = 一致性测试；不是'合规'（compliance） |
| `steward` | 2 | 管家（具名的人类责任人） | steward 必须是自然人（standalone spec 定义） |
| `claimed` | 1 | （未入库） |  |
| `admitted` | 1 | 已受理 | 与 confirmed（已确认效果）区分 |
| `receipt` | 1 | 收据（防篡改的经过记录） | append-only + prevReceipt 链；不是'收条'的泛化 |
| `reconcile` | 1 | （未入库） |  |
| `idempotency` | 1 | 幂等性 | 下游重复执行不产生额外效果；与'恰好一次'不同 |
| `reconciliation` | 1 | 对账（核对原始尝试的结果） | 不确定结果时先对账，不得改写为 refused/open |
| `withdrawal` | 1 | 撤回（人主动收回已报告的决定） | 必须与'机制失效'区分：二者补救方式不同 |
| `supersedes` | 1 | 替代（追加一条新的来覆盖旧的） | 不是'撤销'：历史保留，只追加替代记录 |
| `withdrawn` | 1 | （未入库） |  |
| `sanctioned` | 1 | 已获批准的 | 被动形态，指该动作已有批准 |
| `extension` | 1 | （未入库） |  |
