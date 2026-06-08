# Quick-Absorption Writing

## 一句话定位

quick_absorption 不是摘要、不是解释、不是迷你教案。它是 1-3 句定位描述——告诉学生这个知识点在哪、长什么样、在源材料里怎么找到它。它把 SQLite 池子里的 `knowledge_item` 和 `learning_action` 转写为引导学生回源阅读的简洁路标。

## Related Theories

- **Dual Coding Theory** (Paivio, 1986; see fundamentals/dual-coding.md): Presenting information through both verbal and visual channels improves encoding. The formula/definition is verbal; the through-line is contextual pattern.
- **Signaling Principle** (Mayer, 2005): Learners benefit when essential material is highlighted. The through-line accent signals what to pay attention to.
- **Advance Organizer** (Ausubel): A brief orienting statement before detailed content improves comprehension. The quick_absorption serves as an advance organizer for the source material, not a replacement for it.
- **Cognitive Theory of Multimedia Learning** (Mayer): Avoid extraneous material. Every word in quick_absorption must serve either definition, through-line, or boundary-note function — no filler.

## Pool-to-Prose Mapping

The KP data comes from the SQLite pool (loaded via `kp-query-result.json`). Each pool field informs a specific writing decision:

| Pool Field | Writing Decision |
|-----------|-----------------|
| `knowledge_item` | The core subject — what to name in the first sentence. "布尔代数基本定理" becomes the grammatical subject of sentence 1. |
| `learning_action` | The cognitive verb (区分/应用/分析/判断) that should shape the sentence's orientation. A KP with learning_action "区分X和Y" needs a contrast frame; "应用Z" needs a condition+application frame. |
| `knowledge_type` | Determines the default framing angle: `concept-property` → definition angle (what it is + key properties); `method-modeling` → operational angle (what it does + when to use it); `formula-calculation` → condition+formula angle (prerequisites + the formula itself). |
| `fragile` | If 1, the quick_absorption MUST include a boundary/error note — a third sentence stating when the concept applies and when it does NOT. |
| `difficulty` | Higher difficulty (3+) may warrant an extra sentence for orientation — a bridge phrase connecting this KP to something the student already knows. |

## Through-Line Integration

The quick_absorption's second sentence must echo the through-line selected in `02_analysis/through-line-selection.md`. The through-line is the chapter's recurring pattern — a single conceptual thread that ties disparate KPs together.

If the through-line is "逻辑等价变换", every KP's quick_absorption should connect to that thread using this pattern:

> "[KP核心] + 这是 [through-line描述] 的一个环节/体现/应用"

Examples:
- Through-line: "逻辑等价变换" → "化简逻辑表达式时，将复杂项替换为等价简单项。这是逻辑等价变换在简化环节的体现。"
- Through-line: "边界积分→区域积分" → "格林公式将闭曲线积分转为二重积分。与后续高斯、斯托克斯公式共享同一操作模式：边界积分→区域积分。"

If a KP has no apparent connection to the through-line, that gap is significant — document it in the `forbidden_rendering` column of the structure plan.

## Config Override Rules

The student's natural language intent (captured in `01_inputs/view-scope.md`) modifies how quick_absorption is written:

| Config Value | Writing Adjustment |
|-------------|-------------------|
| "快速扫一遍" | 1 sentence max per KP. Lighter wording. Omit through-line sentence unless it adds essential orientation. |
| "重点看第X节" | Standard 1-3 sentence rule for priority sections. 1 sentence for non-priority sections. |
| "详细" | Can use all 3 sentences. Add multi-angle perspective on fragile KPs. |
| "不要MCQ但KP要详细" | More prose depth allowed since no question takes space. Still capped at 3 sentences. |

## The 1-3 Sentence Rule

Every quick_absorption follows this sentence budget:

- **Sentence 1:** Clean statement of what the KP is. Formula/definition/name + context. This is the "locator beacon."
- **Sentence 2:** Through-line connection — how this KP fits the chapter's recurring pattern.
- **Sentence 3 (optional):** Application condition or boundary note — when to use this KP / when NOT to use this KP. Required for fragile=1 KPs.

**Character budget:** Max 120 Chinese characters total. Formula-heavy, algorithm-heavy, or implementation-heavy KPs are exempt from the character limit but NOT exempt from the sentence limit.

## Writing Self-Check

Before approving any quick_absorption, the agent must answer three questions:

1. **Source-direction check:** Does this tell the student what to look for in the source? (Not: does it explain everything?)
2. **Source-dependency check:** Can the student read this and still need to open the textbook? (Not: does it replace the textbook?)
3. **Through-line check:** Does it echo the through-line? (Not: is it generic?)

If the answer to any question is "no," rewrite.

## Teaching Application

- Two-part structure is non-negotiable:
  1. **Clean definition/formula statement** — factual, concise, source-grounded
  2. **Through-line accent** — one sentence choosing a perspective that recurs across the chapter
- The through-line must NOT explain what the definition means. It must point to a pattern the student will see again.
- Bad: "格林公式把闭曲线积分转为二重积分。使用时要先确认方向。" (This explains — it's a mini-lesson)
- Good: "格林公式将闭曲线积分转为区域二重积分：∮Pdx+Qdy = ∬(Q_x-P_y)dσ。与后续高斯、斯托克斯公式共享同一操作模式：边界积分→区域积分。" (Definition + recurring pattern)
- Length: normally 1-3 sentences. If you need more, your through-line may be too vague.

## Aha Moment

> The hardest part of writing quick_absorption is NOT explaining. Your instinct as an educator is to clarify, elaborate, connect. Resist it. The student's job is to read the source. Your job is to tell them what to look for.

## In-workflow Application

- `03_plans/structure-plan.md`: The quick_absorption field in the KP-Level Rendering Plan
- `04_checks/` gates: coverage.md verifies all KPs have quick_absorption; mcq-quality.md verifies questions are source-dependent (not answerable from quick_absorption alone)
- `skills/through-line-selection.md`: Provides the through-line perspective that feeds sentence 2
- `01_inputs/view-scope.md`: Student config that determines sentence budget and depth override
