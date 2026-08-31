# chinese-copywriting skill

> 语言：[繁体中文](SKILL-README.md) ｜ [English](SKILL-README.en.md) ｜ **简体中文**

把《中文文案排版指北》做成 AI 编码代理可直接使用的 skill，附一支零依赖的检查脚本。

支持 Claude Code、Codex CLI、Copilot CLI、OpenCode、Cursor 等读取 `skills/` 目录的工具。

## 这个 skill 做什么

只管**排版层**：空格、全角半角、标点形制、名词写法。

| 做 | 不做 |
| --- | --- |
| 中英文、中文与数字、数字与单位之间的空格 | 错别字校订 |
| 全角与半角标点的形制 | 文句润饰、改写 |
| 重复标点 | 去除 AI 痕迹 |
| 专有名词大小写、不地道的缩写 | 翻译 |

不动字句与内容。遇到职责以外的需求，skill 会说明并交给对应的工具。

## 安装

### 方法一：ai-global（推荐）

[ai-global](https://github.com/lazyjerry/ai-global) 会把 skill 装进中央目录，再一次投影给所有 AI 工具，不必每个工具各复制一份。

```bash
ai-global add-skill lazyjerry/chinese-copywriting-guidelines
ai-global relink
```

`add-skill` 会自动扫出 repo 里含 `SKILL.md` 的目录，实体放进 `~/.ai-global/v-skills/lazyjerry/chinese-copywriting-guidelines/chinese-copywriting/`，各工具读的是投影出去的 symlink。

只装在单一项目就加 `-p`：

```bash
ai-global -p add-skill lazyjerry/chinese-copywriting-guidelines
```

常用的后续操作：

| 命令 | 用途 |
| --- | --- |
| `ai-global list-skills` | 列出已安装的 skill 分类树 |
| `ai-global update-skills` | 依安装记录重新拉取更新 |
| `ai-global disable chinese-copywriting` | 暂时停用，实体与记录都保留 |
| `ai-global enable chinese-copywriting` | 解除停用 |
| `ai-global remove-skill lazyjerry/chinese-copywriting-guidelines` | 移除并清除安装记录 |

**要修改 skill 内容请改 `v-skills` 底下那份**，`~/.ai-global/skills/` 只是扁平的 symlink 投影层。

### 方法二：手动安装

各家工具的 skills 目录都只认第一层，把整个 `chinese-copywriting` 目录放进去即可：

| 工具 | 全局 | 项目 |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Codex CLI | `~/.agents/skills/` | `.agents/skills/` |
| Copilot CLI | `~/.copilot/skills/` | `.github/skills/` |
| OpenCode | `~/.config/opencode/skills/` | `.claude/skills/` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` |

以 Claude Code 全局安装为例：

```bash
git clone https://github.com/lazyjerry/chinese-copywriting-guidelines.git
cp -r chinese-copywriting-guidelines/skills/chinese-copywriting ~/.claude/skills/
```

改建 symlink 的话，之后 `git pull` 就能同步更新：

```bash
cd chinese-copywriting-guidelines
ln -s "$(pwd)/skills/chinese-copywriting" ~/.claude/skills/chinese-copywriting
```

### 确认装好了

在代理里输入「帮我校对这份文案的排版」，看它有没有进入校对流程。或直接跑脚本：

```bash
python3 ~/.claude/skills/chinese-copywriting/scripts/check_copywriting.py --help
```

## 使用

### 校对模式

跟代理说「校对」「排版检查」「检查中英文空格」，或指名某份中文文档要求检查格式。

流程刻意把确认点放在最前面，**开跑之前一次问完两件事**：

1. **校对哪个文件** — 默认是编辑器当前打开的文件，会标示「（当前打开）」放在第一个选项。消息里已指定路径就直接用。
2. **查完要怎么处理** — 自动修正可安全处理的项目、全部修正、只出报告不改文件，或先看清单再决定。

**绝不自动改文件，也绝不未经确认就开跑。** 未取得同意之前不会执行带 `--fix` 的命令。

报告的每一条违规都会附引用参考，指回唯一事实根据：

```text
{规则名称} L{起始行}-L{结束行}
```

例如 `数字与单位之间需要增加空格 L52-L74`。行号查的是上游 README，不是自行推算。

校对排版规则文档时（例如本项目的 `README*.md`），`错误：` 底下的示范句是刻意写错的教材，skill 不会修正它们，并会与真违规分开列。

### 撰写模式

请代理产出中文文案时，排版规则直接套用，不出报告、不询问、不附引用参考。

### 只用检查脚本

脚本零依赖，不需要 AI 代理也能单独使用：

```bash
# 只报告，有违规时 exit code 为 1
python3 skills/chinese-copywriting/scripts/check_copywriting.py <文件>

# 就地修正
python3 skills/chinese-copywriting/scripts/check_copywriting.py --fix <文件>

# 机器可读输出
python3 skills/chinese-copywriting/scripts/check_copywriting.py --json <文件>

# 一并检查〈争议〉一节的两条规则
python3 skills/chinese-copywriting/scripts/check_copywriting.py --dispute <文件>
```

`--fix` 只处理可安全机械判定的规则：中英文与数字之间的空格、数字与单位之间的空格、全角标点旁多余的空白、重复的标点、全角数字。大小写、不地道的缩写等需要语义判断的项目一律只报告。

脚本会自动跳过代码块、行内代码的内容、URL、Markdown 链接目标与表格分隔线、HTML 标签属性，以及 YAML frontmatter。

**脚本本身不做交互确认**，这样才进得了 CI；「问用户要不要修」是 skill 流程的责任。

## 规则与引用来源

12 条规则的完整正误范例、行号索引与例外索引都在
[skills/chinese-copywriting/references/rules.md](skills/chinese-copywriting/references/rules.md)。

行号的唯一事实根据是上游 README：

<https://github.com/sparanoid/chinese-copywriting-guidelines/blob/master/README.md>

本项目 `README.md` 第 1 至 266 行与上游逐字相同，所以同一组行号两边都适用。核对基准记在 `references/rules.md` 开头，上游改版后要重新核对。

## 开发

### 目录

```
skills/chinese-copywriting/
├─ SKILL.md                    流程、引用规范、报告样板
├─ references/rules.md         唯一事实根据、规则索引、例外索引、12 条细则
└─ scripts/check_copywriting.py

skill-tests/                   三层测试，见下
```

### 改东西要动哪几份

| 想改的东西 | 要动的文件 | 收尾 |
| --- | --- | --- |
| 校对流程、报告格式 | `SKILL.md` | 跑排版自检 |
| 规则细则、行号索引 | `references/rules.md` | 跑 `test_citations.py` |
| 检测或修正逻辑 | `scripts/check_copywriting.py` | 跑全部测试 |
| 测试样本 | `skill-tests/script/cases/` | 跑 `regenerate_cases.py` |
| 已知缺陷清单 | `skill-tests/script/gaps.py` | 跑 `regenerate_cases.py` 与 `regenerate_known_gaps.py` |

三支生成器维护三份生成文件，不要手改生成文件：

```bash
python3 skill-tests/script/regenerate_cases.py       # cases.json
python3 skill-tests/script/regenerate_known_gaps.py  # KNOWN-GAPS.md
python3 skill-tests/script/regenerate_citations.py   # citations-baseline.json
```

`regenerate_citations.py` 是唯一需要停下来想一下的：哈希对不上代表上游 README 改了，要先确认 `references/rules.md` 的行号与细则要不要跟着改，**不要直接覆盖基准了事**。

### 文档本身也要合规

改完说明文档，拿自己的脚本扫一遍：

```bash
python3 skills/chinese-copywriting/scripts/check_copywriting.py \
  SKILL-README.md skills/chinese-copywriting/SKILL.md
```

`skill-tests/script/cases/` 与 `skill-tests/evals/fixtures/` 底下的文件**故意违反排版规则**，是测试数据不是文档，已由 `.remarkignore` 排除，不要「顺手修好」。

## 测试

```bash
bash skill-tests/run-script-tests.sh               # 绿灯 + 红灯，秒回、无网络
bash skill-tests/run-script-tests.sh --green-only  # 只跑绿灯，开发时用
bash skill-tests/evals/run-evals.sh                # 模型行为，慢、有 API 成本
bash skill-tests/check-upstream-drift.sh           # 可选，需网络
```

三层各自解决不同问题：

| 层 | 测什么 |
| --- | --- |
| 绿灯 | 锁住检查脚本现行**正确**的行为，含刻意不做的事 |
| 红灯 | 标出脚本**还做不到**的事 |
| eval | 模型有没有照 `SKILL.md` 的约定做事 |

### 红灯现在是红的

这是刻意的。红灯没有用 `expectedFailure` 盖掉——把红灯藏成绿色等于没测。脚本目前有一批已知缺陷，逐条列在
[skill-tests/KNOWN-GAPS.md](skill-tests/KNOWN-GAPS.md)，修好一条对应的红灯就会自己转绿。

修好之后的完整循环：

1. 改 `scripts/check_copywriting.py`
2. 把修好的那笔从 `skill-tests/script/gaps.py` 删掉
3. 跑 `regenerate_cases.py` 与 `regenerate_known_gaps.py`
4. 重跑测试，绿灯应全过、红灯少一条

**修好脚本之后绿灯会先变红**，因为快照还停在旧行为。失败消息会告诉你重跑生成器，这不是缺陷。

### 加一个测试案例

写一份 `skill-tests/script/cases/case-*.md`，在 `regenerate_cases.py` 的 `TITLES` 补一行，然后跑生成器。测试逻辑读数据，不必动 Python。

细节见 [skill-tests/README.md](skill-tests/README.md) 与 [skill-tests/evals/README.md](skill-tests/evals/README.md)。

## 许可

与本项目相同，见 [LICENSE](LICENSE)。
