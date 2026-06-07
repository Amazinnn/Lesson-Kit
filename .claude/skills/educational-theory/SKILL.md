---
name: educational-theory
description: >-
  Educational theory reference for instructional workflow design. Use when designing or improving
  any aspect of the academic materials automation workflow: creating MCQ questions, choosing
  through-line perspectives, deciding knowledge granularity, sequencing content, writing knowledge
  statements, designing feedback mechanisms, or making any pedagogical design decision.
  This skill provides the theoretical foundation for WHY certain design choices work better
  than others. Always consult relevant scenario cards before finalizing a pedagogical decision.
  Trigger phrases: "教学设计", "教育理论", "pedagogy", "learning theory", "how should I teach this",
  "认知负荷", "测试效应", "教学法", or when making any instructional design decision.
  This skill is for the WORKFLOW DESIGNER (Claude Code) — not for downstream lesson-generation agents.
---

# Educational Theory Reference

You are an educator-engineer. These theories are not rigid rules — they are lenses that help you see each instructional design decision from multiple angles before committing.

## How to Use This Reference

1. Identify the **design scenario** you're in (MCQ design? Content sequencing? Knowledge framing?)
2. Open the corresponding card in `repertoire/` for practical guidance
3. When a card references a fundamental theory, open it in `fundamentals/` for depth
4. When you need creative inspiration, browse `aha-moments/` for cross-domain insights

## Index

### Repertoire (by Design Scenario)
| Scenario | Card | Key Theories |
|----------|------|-------------|
| Designing MCQs | `repertoire/mcq-design.md` | testing effect, error-driven learning, cognitive diagnosis, ICAP |
| Choosing through-line perspectives | `repertoire/through-line-selection.md` | advance organizer, elaboration theory, structural scaffolding |
| Sequencing content | `repertoire/content-sequencing.md` | cognitive load theory, progressive differentiation, spiral curriculum |
| Determining knowledge granularity | `repertoire/knowledge-granularity.md` | chunking, working memory limits, learnable unit theory |
| Writing knowledge statements (quick_absorption) | `repertoire/knowledge-framing.md` | dual coding, signaling principle, cognitive theory of multimedia learning |
| Designing feedback | `repertoire/feedback-design.md` | formative assessment, feedback timing, Hattie feedback types, error-driven learning |
| Structuring practice & exercises | `repertoire/practice-structuring.md` | retrieval practice, spacing, interleaving, deliberate practice |
| Using examples & analogies | `repertoire/example-analogy-use.md` | worked examples, analogical reasoning, expertise reversal effect |
| Motivating learners | `repertoire/motivation-design.md` | expectancy-value theory, self-determination theory, growth mindset |

### Fundamentals (Cognitive Principles)
| Theory | File | Source |
|--------|------|--------|
| Cognitive Load Theory | `fundamentals/cognitive-load-theory.md` | Sweller (1988–2025) |
| Testing Effect (Retrieval Practice) | `fundamentals/testing-effect.md` | Roediger & Karpicke (2006–2025) |
| Spacing Effect & Distributed Practice | `fundamentals/spacing-effect.md` | Ebbinghaus (1885)–Cepeda (2006–2025) |
| Desirable Difficulties | `fundamentals/desirable-difficulties.md` | Bjork & Bjork (1994–2025) |
| Dual Coding & Multimedia Learning | `fundamentals/dual-coding.md` | Paivio (1986); Mayer (2001–2025) |
| ICAP Framework | `fundamentals/icap-framework.md` | Chi & Wylie (2014–2024) |
| Feedback for Learning | `fundamentals/feedback-learning.md` | Hattie & Timperley (2007–2023) |
| Schema Theory | `fundamentals/schema-theory.md` | Bartlett (1932)–Sweller (2025) |
| Metacognition & Self-Regulation | `fundamentals/metacognition.md` | Flavell (1979)–Ambrose (2010) |
| Merrills First Principles | `fundamentals/merrill-first-principles.md` | Merrill (2002–2024) |
| Motivation & Engagement | `fundamentals/motivation-theories.md` | Deci & Ryan (2000)–Dweck (2006) |
| Prior Knowledge & Transfer | `fundamentals/prior-knowledge-transfer.md` | Ambrose (2010)–Bransford (2000) |

### Aha Moments (Cross-Domain Insights)
| Insight | File |
|---------|------|
| The Curse of Knowledge | `aha-moments/curse-of-knowledge.md` |
| Productive Failure | `aha-moments/productive-failure.md` |
| Illusions of Knowing | `aha-moments/illusions-of-knowing.md` |
| The Generation Effect | `aha-moments/generation-effect.md` |
| The Expertise Reversal Effect | `aha-moments/expertise-reversal.md` |

## Card Format

Each repertoire card follows this structure:

```
# [Scenario Title]

## 一句话定位
What this scenario is really about.

## Related Theories
Key theories with one-sentence takeaways.

## Teaching Application
Actionable principles derived from the theories.

## Aha Moment
A counterintuitive insight.

## In-workflow Application
Specific files and steps in this workflow.
```

Each fundamentals card:

```
# [Theory Name]

## Core Claim
One-paragraph statement.

## Key Research
Landmark studies and recent evidence.

## Effect Size & Confidence
Meta-analytic range and confidence level.

## Boundary Conditions
When this theory does NOT apply.

## Practical Implications
What this means for design decisions.

## Connection to Other Theories
How it relates to others in the reference.
```

Each aha-moment card:

```
# [Insight Title]

2-3 sentence insight.

## Why This Matters

## Source

## How It Connects
```
