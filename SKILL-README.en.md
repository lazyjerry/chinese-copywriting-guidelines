# chinese-copywriting skill

> Languages: [繁體中文](SKILL-README.md) ｜ **English** ｜ [简体中文](SKILL-README.zh-Hans.md)

Chinese Copywriting Guidelines packaged as a skill for AI coding agents, with a zero-dependency checker script.

Works with Claude Code, Codex CLI, Copilot CLI, OpenCode, Cursor, and any other tool that reads a `skills/` directory.

## What this skill does

Typesetting only: spacing, fullwidth versus halfwidth, punctuation form, how names are written.

| Does | Does not |
| --- | --- |
| Spacing between Chinese and Latin text, numbers, and units | Fix typos |
| Fullwidth and halfwidth punctuation form | Polish or rewrite sentences |
| Duplicate punctuation | Strip AI writing patterns |
| Capitalization of proper nouns, unidiomatic abbreviations | Translate |

It never touches wording or content. When a request falls outside that scope, the skill says so and hands it to the right tool.

## Installation

### Option 1: ai-global (recommended)

[ai-global](https://github.com/lazyjerry/ai-global) installs a skill into one central directory and projects it out to every AI tool at once, so you do not copy it per tool.

```bash
ai-global add-skill lazyjerry/chinese-copywriting-guidelines
ai-global relink
```

`add-skill` scans the repository for directories containing a `SKILL.md`, stores the real files under `~/.ai-global/v-skills/lazyjerry/chinese-copywriting-guidelines/chinese-copywriting/`, and each tool reads a symlink projected from there.

Add `-p` to install into a single project instead:

```bash
ai-global -p add-skill lazyjerry/chinese-copywriting-guidelines
```

Useful follow-ups:

| Command | Purpose |
| --- | --- |
| `ai-global list-skills` | List installed skills as a category tree |
| `ai-global update-skills` | Re-pull updates from the recorded sources |
| `ai-global disable chinese-copywriting` | Disable it; files and records are kept |
| `ai-global enable chinese-copywriting` | Re-enable it |
| `ai-global remove-skill lazyjerry/chinese-copywriting-guidelines` | Remove it and clear the install record |

**Edit the copy under `v-skills`**, not `~/.ai-global/skills/` — that one is only a flat symlink projection layer.

### Option 2: manual install

Every agent only scans the first level of its skills directory, so drop the whole `chinese-copywriting` directory in:

| Agent | Global | Project |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Codex CLI | `~/.agents/skills/` | `.agents/skills/` |
| Copilot CLI | `~/.copilot/skills/` | `.github/skills/` |
| OpenCode | `~/.config/opencode/skills/` | `.claude/skills/` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` |

Installing globally for Claude Code:

```bash
git clone https://github.com/lazyjerry/chinese-copywriting-guidelines.git
cp -r chinese-copywriting-guidelines/skills/chinese-copywriting ~/.claude/skills/
```

Or symlink it instead, so `git pull` keeps it up to date:

```bash
cd chinese-copywriting-guidelines
ln -s "$(pwd)/skills/chinese-copywriting" ~/.claude/skills/chinese-copywriting
```

### Verifying the install

Ask the agent to proofread the typesetting of some Chinese copy and see whether it enters the proofreading workflow. Or run the script directly:

```bash
python3 ~/.claude/skills/chinese-copywriting/scripts/check_copywriting.py --help
```

## Usage

### Proofreading mode

Ask the agent to proofread, check typesetting, or check spacing between Chinese and Latin text — or just name a Chinese document and ask for a format check.

The confirmation step sits at the very front. **Both questions are asked before anything runs**:

1. **Which file** — the file currently open in your editor is the default, marked as the first option. If your message already names a path, that path is used.
2. **What to do with the findings** — auto-fix what is mechanically safe, fix everything, report only, or show the list first and decide afterwards.

**It never edits files on its own, and never starts before you confirm.** No `--fix` runs until you approve it.

Every reported violation carries a citation back to the single source of truth:

```text
{rule name} L{start}-L{end}
```

For example `數字與單位之間需要增加空格 L52-L74`. Line numbers are looked up in the index, never guessed.

When proofreading the guidelines themselves (this repository's `README*.md`, say), the examples under `錯誤：` are deliberately wrong teaching material. The skill leaves them alone and lists them separately from real violations.

### Writing mode

When you ask the agent to produce Chinese copy, the rules are applied directly — no report, no questions, no citations.

### Checker script only

The script has no dependencies and works standalone, no agent required:

```bash
# Report only; exits 1 when violations are found
python3 skills/chinese-copywriting/scripts/check_copywriting.py <file>

# Fix in place
python3 skills/chinese-copywriting/scripts/check_copywriting.py --fix <file>

# Machine-readable output
python3 skills/chinese-copywriting/scripts/check_copywriting.py --json <file>

# Also check the two rules from the Dispute section
python3 skills/chinese-copywriting/scripts/check_copywriting.py --dispute <file>
```

`--fix` only touches rules that can be decided mechanically: spacing between Chinese and Latin text or numbers, spacing between numbers and units, stray whitespace around fullwidth punctuation, duplicate punctuation, and fullwidth digits. Capitalization, jargon and anything else needing judgement is reported but never rewritten.

The script skips code blocks, inline code contents, URLs, Markdown link targets and table delimiters, HTML attributes, and YAML frontmatter.

**The script itself never prompts**, which is what makes it usable in CI. Asking whether to apply fixes is the skill workflow's job.

## Rules and citation source

The full correct and incorrect examples for all 12 rules, the line-number index and the exception index live in
[skills/chinese-copywriting/references/rules.md](skills/chinese-copywriting/references/rules.md).

Line numbers are anchored to the upstream README, the single source of truth:

<https://github.com/sparanoid/chinese-copywriting-guidelines/blob/master/README.md>

Lines 1 to 266 of this repository's `README.md` are byte-identical to upstream, so the same line numbers apply to both. The verified baseline is recorded at the top of `references/rules.md`; re-check it whenever upstream changes.

## Development

### Layout

```
skills/chinese-copywriting/
├─ SKILL.md                    workflow, citation rules, report template
├─ references/rules.md         source of truth, rule index, exception index, 12 rules in detail
└─ scripts/check_copywriting.py

skill-tests/                   three test layers, see below
```

### What to touch for what

| What you want to change | File to edit | Follow up with |
| --- | --- | --- |
| Proofreading workflow, report format | `SKILL.md` | Run the typesetting self-check |
| Rule details, line-number index | `references/rules.md` | Run `test_citations.py` |
| Detection or fixing logic | `scripts/check_copywriting.py` | Run every test |
| Test samples | `skill-tests/script/cases/` | Run `regenerate_cases.py` |
| Known-gap list | `skill-tests/script/gaps.py` | Run `regenerate_cases.py` and `regenerate_known_gaps.py` |

Three generators maintain three generated files. Do not hand-edit the generated ones:

```bash
python3 skill-tests/script/regenerate_cases.py       # cases.json
python3 skill-tests/script/regenerate_known_gaps.py  # KNOWN-GAPS.md
python3 skill-tests/script/regenerate_citations.py   # citations-baseline.json
```

`regenerate_citations.py` is the one to pause over: a hash mismatch means the upstream README changed, so first decide whether the line numbers and rule details in `references/rules.md` need to change too. **Do not just overwrite the baseline.**

### The docs follow the rules too

After editing documentation, run the project's own checker over it:

```bash
python3 skills/chinese-copywriting/scripts/check_copywriting.py \
  SKILL-README.md skills/chinese-copywriting/SKILL.md
```

Files under `skill-tests/script/cases/` and `skill-tests/evals/fixtures/` **violate the rules on purpose**. They are test data, not documentation, already excluded through `.remarkignore`. Do not tidy them up.

## Testing

```bash
bash skill-tests/run-script-tests.sh               # green + red, fast and offline
bash skill-tests/run-script-tests.sh --green-only  # green only, for day-to-day work
bash skill-tests/evals/run-evals.sh                # model behaviour, slow, costs API credits
bash skill-tests/check-upstream-drift.sh           # optional, needs network
```

Each layer solves a different problem:

| Layer | What it covers |
| --- | --- |
| Green | Locks in the checker's currently **correct** behaviour, including what it deliberately leaves alone |
| Red | Marks what the checker **cannot do yet** |
| Eval | Whether the model follows the agreements in `SKILL.md` |

### The red layer is red right now

That is deliberate. Red tests are not wrapped in `expectedFailure` — hiding red behind green is the same as not testing. The checker has a batch of known defects, listed one by one in
[skill-tests/KNOWN-GAPS.md](skill-tests/KNOWN-GAPS.md). Fix one and its red test turns green on its own.

The full cycle after a fix:

1. Edit `scripts/check_copywriting.py`
2. Delete that entry from `skill-tests/script/gaps.py`
3. Run `regenerate_cases.py` and `regenerate_known_gaps.py`
4. Re-run the tests: green should still pass, red should be one shorter

**Green goes red first after you fix the script**, because the snapshot still holds the old behaviour. The failure message tells you to re-run the generator. That is not a defect.

### Adding a test case

Write a `skill-tests/script/cases/case-*.md`, add a line to `TITLES` in `regenerate_cases.py`, then run the generator. The test logic reads the data, so no Python changes are needed.

More detail in [skill-tests/README.md](skill-tests/README.md) and [skill-tests/evals/README.md](skill-tests/evals/README.md).

## License

Same as this project, see [LICENSE](LICENSE).
