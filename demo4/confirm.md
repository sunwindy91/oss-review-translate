# 英文确认草稿（发帖前必须先问自己：这几点我真的读对了吗）

I want to make sure I have read your points correctly before responding — could you confirm or correct the following?

- **[P01]** You wrote: "Thanks @sunwindy91 and @gomission for the careful, concrete feedback. I would be glad to collaborate on turning these cases into clearer requirements and test vectors. As in my earlier reply, what follows are proposed cl…" — my understanding: _(fill in one sentence)_
  - _must verify_: 否定词 2 处 —— 作用域易被机翻搬动（not A and B ≠ not (A and B)）
- **[P02]** You wrote: "**Cardinality (@sunwindy91).** You're right: this is a real gap in the published text. The binding has per-sanction `validUntil`, an `effectNotBefore` delay, and `lapsed` for a window that elapses unused, but it does not…" — my understanding: _(fill in one sentence)_
  - _must verify_: 否定词 2 处 —— 作用域易被机翻搬动（not A and B ≠ not (A and B)）
- **[P03]** You wrote: "**Unknown outcome after dispatch (@gomission).** Agreed: “admitted / allowance spent” and “effect confirmed / unknown” are separate facts. Your five-step vector makes the distinction concrete: persist admission and claim…" — my understanding: _(fill in one sentence)_
- **[P04]** You wrote: "The receipt example already includes separate `dispatchedAt` and `effectAt` fields (§6.2), but the text still needs explicit allowance and recovery semantics. Proposed: uncertainty after dispatch MUST NOT restore the all…" — my understanding: _(fill in one sentence)_
  - _must verify_: 强制/禁止语气：强制（MUST）(MUST) / 禁止（MUST NOT）(MUST NOT) / 强制（MUST）(MUST) / 禁止（MUST NOT）(MUST NOT) —— 中文必须对应为 必须/不得，不可降级为『应当/可以』; 否定词 4 处 —— 作用域易被机翻搬动（not A and B ≠ not (A and B)）; 数字/计数：、exactly、once（逐字核对）
- **[P05]** You wrote: "**Withdrawal versus mechanism failure (@sunwindy91).** Today `open` with `supersedes` records that a reported decision was withdrawn, without saying why. A human withdrawing a decision and a mechanism failing to enforce …" — my understanding: _(fill in one sentence)_
  - _must verify_: 否定词 3 处 —— 作用域易被机翻搬动（not A and B ≠ not (A and B)）
- **[P06]** You wrote: "**Independently checkable class basis.** The binding already treats a peer's `class` as an untrusted claim and resolves ambiguity upward (§10), but the examples' `classBasis` is just a rule label. Proposed: the classific…" — my understanding: _(fill in one sentence)_
- **[P07]** You wrote: "**Q1 / Q3.** The risk of substituting the caller for the named steward is a useful behavioural argument for `AUTH_REQUIRED`. As clarified earlier, an unaware client encountering a required but unactivated extension shoul…" — my understanding: _(fill in one sentence)_
- **[P08]** You wrote: "On sharing code: thank you for offering. For now, please hold off on sending the implementation or test suite. Short, implementation-independent cases as issues in [math-r-association/sanction-gate](https://github.com/ma…" — my understanding: _(fill in one sentence)_

If any of the above is a misreading, please say so and I will re-read the thread; I would rather correct my understanding now than reply on a wrong reading.

— drafted by oss-review-translate for a2aproject/A2A#2250
