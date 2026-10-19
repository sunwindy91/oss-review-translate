# [Extension Proposal] Sanction Gate — bounded human authorisation for irreversible actions

https://github.com/a2aproject/A2A/issues/2250 · OPEN · 抽取 2026-10-19T22:00:10+00:00

> 段落 15 · **高风险 8** · 中 29 · 低 4　（默认只显示高风险，`--all-flags` 看全部）
> ⚠️ 段落数不匹配：原文 15 段，译文 9 段——逐段核对前请先手工对齐


### [P01]

**EN（原文）**

> Thanks @sunwindy91 and @gomission for the careful, concrete feedback. I would be glad to collaborate on turning these cases into clearer requirements and test vectors. As in my earlier reply, what follows are proposed clarifications for a future revision of the binding, not changes to the published text or validated behaviour. There is no reference implementation, and I can't commit to a revision timeline.

**ZH（你的译文）**

感谢 @sunwindy91 与 @gomission 细致、具体的反馈。我很乐意合作，把这些案例转化为更清晰的需求与测试向量。与我先前的回复一样，以下内容是为**未来某一版修订**提出的澄清，**不是**对已发布文本的修改，也**不是**已验证的行为。目前没有参考实现，我也无法承诺修订时间表。

**⚠️ 风险标记**
- [high] 否定词 2 处 —— 作用域易被机翻搬动（not A and B ≠ not (A and B)）

*（另有 1 条中/低风险，--all-flags 查看）*


### [P02]

**EN（原文）**

> **Cardinality (@sunwindy91).** You're right: this is a real gap in the published text. The binding has per-sanction `validUntil`, an `effectNotBefore` delay, and `lapsed` for a window that elapses unused, but it does not say whether one admission authorises one crossing or many. The emergency path (§10) is the only place with an explicit budget. Proposed clarification: a sanction remains bound to one exact `proposalHash`, and its admission authorises a single dispatch unless an explicit use budget is specified. A validity window bounds time; it does not grant additional uses. The allowance must be durably claimed before dispatch, rather than consumed only when an effect is confirmed.

**ZH（你的译文）**

**次数（@sunwindy91）。** 你说得对：这是已发布文本里的一个**真实缺口**。约束性规范文本里有逐条批准的 `validUntil`、`effectNotBefore` 延迟，以及用于"窗口空耗未使用"的 `lapsed`，但它**没有**说明：一次受理是授权一次穿越，还是多次。紧急路径（§10）是唯一有显式预算的地方。建议的澄清是：一条批准仍绑定到某个确切的 `proposalHash`，其受理**只授权一次派发**，除非另有明确的用量预算。有效期约束的是**时间**；它**不额外授予**使用次数。额度必须在**派发之前**就持久地占用，而不是只在效果被确认时才消费。

**⚠️ 风险标记**
- [high] 否定词 2 处 —— 作用域易被机翻搬动（not A and B ≠ not (A and B)）

*（另有 4 条中/低风险，--all-flags 查看）*


### [P03]

**EN（原文）**

> **Unknown outcome after dispatch (@gomission).** Agreed: “admitted / allowance spent” and “effect confirmed / unknown” are separate facts. Your five-step vector makes the distinction concrete: persist admission and claim the allowance; dispatch once; lose the acknowledgement or outcome record; restart and request the same action; observe **no second dispatch**, with the allowance still spent and the original outcome unresolved.

**ZH（你的译文）**

**派发后的结果未知（@gomission）。** 同意：「已受理／额度已占用」与「效果已确认／未知」是**两件独立的事实**。你的五步向量把这一区分变得具体：持久化受理并占用额度；派发一次；丢失确认或结果记录；重启并请求同一动作；观察到**没有第二次派发**，额度仍为已占用，且原始结果仍未解决。

*（3 条中/低风险已隐藏，--all-flags 查看）*


### [P04]

**EN（原文）**

> The receipt example already includes separate `dispatchedAt` and `effectAt` fields (§6.2), but the text still needs explicit allowance and recovery semantics. Proposed: uncertainty after dispatch MUST NOT restore the allowance and MUST NOT rewrite the gate outcome as `refused` or `open`; reconcile the original attempt before any new decision. Multiple workers would need a shared atomic claim. That does not establish exactly-once downstream effects: downstream idempotency or reconciliation remains a separate requirement. I am treating your scenario as a proposed test vector, not as evidence of A2A/Sanction Gate conformance.

**ZH（你的译文）**

收据示例已经包含分开的 `dispatchedAt` 与 `effectAt` 字段（§6.2），但文本仍然需要显式的额度与恢复语义。建议：派发后的不确定性**不得**恢复额度，也**不得**把闸门结局改写为 `refused` 或 `open`；在做任何新决定之前，必须先核对原始尝试。多个工作者需要一个共享的原子占用。这并**不**能确立下游的"恰好一次"效果：下游的幂等性或对账仍是单独的要求。我把你的场景视为一个**建议的测试向量**，而不是 A2A／Sanction Gate 一致性的证据。

**⚠️ 风险标记**
- [high] 强制/禁止语气：强制（MUST）(MUST) / 禁止（MUST NOT）(MUST NOT) / 强制（MUST）(MUST) / 禁止（MUST NOT）(MUST NOT) —— 中文必须对应为 必须/不得，不可降级为『应当/可以』
- [high] 否定词 4 处 —— 作用域易被机翻搬动（not A and B ≠ not (A and B)）
- [high] 数字/计数：、exactly、once（逐字核对）

*（另有 3 条中/低风险，--all-flags 查看）*


### [P05]

**EN（原文）**

> **Withdrawal versus mechanism failure (@sunwindy91).** Today `open` with `supersedes` records that a reported decision was withdrawn, without saying why. A human withdrawing a decision and a mechanism failing to enforce one require different remediation. A superseding correction must distinguish those reasons and preserve the original history; it must not imply that a human withdrew when the gate was actually absent from the execution path. That enforcement failure also needs to remain visible as a failure, not be disguised as a steward decision.

**ZH（你的译文）**

**撤回 vs 机制失效（@sunwindy91）。** 目前 `open` 配 `supersedes` 记录的是"一个已报告的决定被撤回"，但**没有说明原因**。人类撤回一个决定，与机制未能执行一个决定，所需的补救方式不同。一条替代性更正**必须**区分这两种原因，并保留原始历史；它**不得**在闸门实际上并不在执行路径上时，暗示是人类撤回了决定。那次执行失效也必须**继续作为失效可见**，而不得被伪装成管家的决定。

**⚠️ 风险标记**
- [high] 否定词 3 处 —— 作用域易被机翻搬动（not A and B ≠ not (A and B)）

*（另有 3 条中/低风险，--all-flags 查看）*


### [P06]

**EN（原文）**

> **Independently checkable class basis.** The binding already treats a peer's `class` as an untrusted claim and resolves ambiguity upward (§10), but the examples' `classBasis` is just a rule label. Proposed: the classification should be recheckable against the actual action and arguments, linked to the sanctioned proposal and the applicable classification rule. A hash can bind that evidence, but a hash alone cannot let a reviewer inspect it; the underlying evidence must be available to the authorised reviewer. Your evasion and content-only false-positive cases would be useful paired vectors.

**ZH（你的译文）**

**可独立核验的类别依据。** 规范文本已经把对端声明的 `class` 当作**不可信输入**，并在有歧义时向上归类（§10），但示例里的 `classBasis` 只是一个规则标签。建议：分类应当能对着**实际的动作与参数**重新核验，并关联到被批准的提案与适用的分类规则。哈希可以绑定这些证据，但**仅有哈希无法让评审者检视**；底层证据必须对获授权的评审者可得。你提到的绕过案例与"仅内容型"的误报案例，会是有用的**配对向量**。

*（6 条中/低风险已隐藏，--all-flags 查看）*


### [P07]

**EN（原文）**

> **Q1 / Q3.** The risk of substituting the caller for the named steward is a useful behavioural argument for `AUTH_REQUIRED`. As clarified earlier, an unaware client encountering a required but unactivated extension should receive `ExtensionSupportRequiredError`; it should not enter the sanction flow. The case for `required: true` rests on the client's obligation to follow that flow.

**ZH（你的译文）**

**Q1 / Q3。** "用调用方顶替具名管家"的风险，是支持 `AUTH_REQUIRED` 的一个有用的**行为论据**。如此前澄清的：不知情的客户端遇到"必需但未激活的扩展"时，应收到 `ExtensionSupportRequiredError`，而**不应**进入批准流程。支持 `required: true` 的理由，建立在客户端**必须遵循该流程**的义务之上。

*（4 条中/低风险已隐藏，--all-flags 查看）*


### [P08]

**EN（原文）**

> On sharing code: thank you for offering. For now, please hold off on sending the implementation or test suite. Short, implementation-independent cases as issues in [math-r-association/sanction-gate](https://github.com/math-r-association/sanction-gate/issues) would be the most useful next step: inputs and preconditions, the event sequence, expected dispatch/effect counts, and the records that should remain after restart or failure. That gives us a common basis for reviewing the text without depending on either implementation.

**ZH（你的译文）**

关于共享代码：感谢你提出。**目前请暂缓**发送实现或测试套件。把简短的、**与实现无关**的案例作为 issue 提交到 [math-r-association/sanction-gate](https://github.com/math-r-association/sanction-gate/issues) 会是最有用的下一步：输入与前置条件、事件序列、期望的派发／效果计数，以及重启或失败后应保留的记录。这样我们就有了一个共同基础，来在不依赖任一实现的前提下评审文本。

*（2 条中/低风险已隐藏，--all-flags 查看）*


### [P09]

**EN（原文）**

> *Prepared with AI assistance; publication authorised by the author.*

**ZH（你的译文）**

*在 AI 协助下撰写；发布已由作者授权。*


### [P10]

**EN（原文）**

> Thanks @sunwindy91 for writing up the three cases and for holding off on the code. Together with @gomission's recovery case, they give us concrete scenarios to discuss:

**ZH（你的译文）**

（待填）

*（2 条中/低风险已隐藏，--all-flags 查看）*


### [P11]

**EN（原文）**

> - [#4](https://github.com/math-r-association/sanction-gate/issues/4): recovery after a lost acknowledgement or outcome record;
> - [#5](https://github.com/math-r-association/sanction-gate/issues/5): classification evasion and content-only false positives;
> - [#6](https://github.com/math-r-association/sanction-gate/issues/6): enforcement missing from the execution path;
> - [#7](https://github.com/math-r-association/sanction-gate/issues/7): expiry and reuse of an allowance by an unrelated action.

**ZH（你的译文）**

（待填）

*（2 条中/低风险已隐藏，--all-flags 查看）*


### [P12]

**EN（原文）**

> These remain proposed test scenarios for a possible future revision, not accepted requirements or conformance results. There is no reference implementation, and I can't commit to a revision timeline. Let's keep the detailed discussion in those issues: what counts as a content operation, how to distinguish activation failure from an enforcement bypass, and how expiry should constrain recovery. Thank you both for making the gaps easier to examine.

**ZH（你的译文）**

（待填）

**⚠️ 风险标记**
- [high] 否定词 2 处 —— 作用域易被机翻搬动（not A and B ≠ not (A and B)）

*（另有 2 条中/低风险，--all-flags 查看）*


### [P13]

**EN（原文）**

> *Prepared with AI assistance.*

**ZH（你的译文）**

（待填）


### [P14]

**EN（原文）**

> Thanks, @sunwindy91 — the revisions to #5, #6 and #7 match the points we raised. We will read the updated issues and comment there if anything is still unclear. As before, these remain proposed test scenarios: the published binding is unchanged, there is no reference implementation, and we cannot commit to a timeline.

**ZH（你的译文）**

（待填）

**⚠️ 风险标记**
- [high] 否定词 2 处 —— 作用域易被机翻搬动（not A and B ≠ not (A and B)）

*（另有 1 条中/低风险，--all-flags 查看）*


### [P15]

**EN（原文）**

> *Prepared with AI assistance.*

**ZH（你的译文）**

（待填）
