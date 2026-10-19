# oss-review-translate

[![test](https://github.com/sunwindy91/oss-review-translate/actions/workflows/test.yml/badge.svg)](https://github.com/sunwindy91/oss-review-translate/actions/workflows/test.yml)

**Review-grade bilingual fidelity for open-source collaboration.** If you read and reply to English issues,
reviews, or specifications in a second language, this tool makes *misreading detectable* instead of hoping it
didn't happen.

**It is not a translator.** Translation can be wrong in ways you cannot see. This tool does not try to be more
accurate — it makes the places where accuracy matters **visible, checkable, and confirmable**.

## The four things translation destroys

| Failure | Real shape | Consequence |
|---|---|---|
| **Obligation strength** | `MUST NOT restore the allowance` rendered as "should not" | a hard prohibition becomes a mild preference |
| **Terminology drift** | `allowance` rendered as quota / budget / permit in five paragraphs | readers think they are three different things |
| **Negation scope** | `must not rewrite as refused or open` read as "not refused, but open is fine" | the conclusion is inverted |
| **Counts** | `one dispatch`, `zero effects`, `exactly once` | a conformance argument silently breaks |

Plus two social ones: politeness read as commitment (`hold off` = *not now*, not *no*), and unmarked AI-assisted
authorship changing how binding a statement is.

## What it produces

Given a thread, it writes a directory with:

| File | What it is |
|---|---|
| `bilingual.md` | source and translation **paired paragraph by paragraph**, each with an anchor like `[P05]`, plus **graded** risk flags (`high` shown by default; `--all-flags` for all) |
| `terms.md` | glossary candidates and which of your locked terms were hit |
| `confirm.md` | an English confirmation draft that quotes only the **high-risk** paragraphs |
| `reply.md` | a **reply scaffold**: write "my understanding / please confirm" per anchored paragraph, then answer, then a pre-post checklist |
| `audit.jsonl` | one line per run: paragraphs, risk counts, how many translations were used, who read it |
| `summary.json` | with `--format json`, for automation / chat cards |

## The protocol

1. **Extract** only what changed (`--since`, `--skip-op`, `--exclude-author`).
2. **Align** — paste your translation, one block per paragraph. A count mismatch is reported, not hidden.
3. **Verify** only the flagged paragraphs against the source: obligation strength, negation scope, counts,
   identifiers, section references.
4. **Confirm** with `confirm.md` *before* writing the substantive reply.
5. **Record** — keep `audit.jsonl` next to what you sent.

## Install and run

```bash
git clone https://github.com/sunwindy91/oss-review-translate.git
cd oss-review-translate
pip install .            # optional: installs the `oss-review-translate` command

# read only new comments, align with your translation, and grade the risks
python oss-review-translate.py --repo owner/name --number 123 \
    --since 2026-10-14 --skip-op --exclude-author <your-handle> \
    --translation zh.txt --out out/

# two independent translations: disagreements are marked per paragraph
python oss-review-translate.py ... --translation zh.txt --translation2 zh2.txt

# fail the pipeline while high-risk paragraphs are unconfirmed (exit code 3)
python oss-review-translate.py ... --fail-on-high
```

Offline and reproducible: `--save-json thread.json` archives the exact thread you read; `--from-json` replays it
with no network. `feishu_card.py summary.json` renders a chat card **without sending it** — posting is an
irreversible outward action, so the tool stops at generating payload plus the command.

## Why not automate the reply

Because a reply is public and cannot be taken back. Automating *reading* is safe; automating *asserting* is how a
misreading becomes someone else's record. The tool deliberately stops at evidence plus a confirmation draft.

## Tests

```bash
python tests/test_flags.py    # unit assertions on the risk taxonomy
python tests/test_all.py      # end-to-end, offline replay (no network, no gh)
```

CI runs both on every push and pull request.

## Limits

- It does not translate; you supply the translation (machine or human).
- Risk detection is heuristic, tuned for English normative text; it will miss things. Missing a term is a signal
  to extend the glossary, not to trust the silence.
- Alignment is paragraph-based; tables and unbroken long blocks may need manual pairing.
- It cannot guarantee you understood correctly. It guarantees that **where you might not have, you can see it**.

MIT licensed. Related: [the methodology note (Chinese)](方案/方法论_跨语种协作的保真读法.md) —
five steps, a risk checklist, and one red line: reading can be automated, asserting cannot.
