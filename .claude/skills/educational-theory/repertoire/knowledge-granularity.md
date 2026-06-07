# Determining Knowledge Granularity

## 一句话定位

知识点粒度的黄金标准：一个小节应该让学生能问自己"我刚才读的那段我读懂了吗"，并能在3-8分钟内得到答案。

## Related Theories

- **Chunking** (Miller, 1956): Working memory can hold approximately 7±2 chunks. Effective instruction organizes content into learnable chunks.
- **Cognitive Load Theory** (see fundamentals/cognitive-load-theory.md): Each knowledge point should represent a single schema that can be acquired without exceeding working memory capacity.
- **Learnable Unit Theory**: A learnable unit is the smallest piece of content that supports a meaningful checkpoint question. Smaller than that → trivial; larger → unfocused.

## Teaching Application

- A knowledge point is too broad if: it covers multiple distinct concepts, needs many pages of source reading, or its MCQ would require a paragraph to answer.
- A knowledge point is too narrow if: it's a single symbol or term, the MCQ is trivial (yes/no without nuance), or it takes under 1 minute to read.
- Practical test: can you write a focused 4-option MCQ where all options are plausible? If not, the granularity is wrong.
- 5-10 KPs per ordinary section; up to 13 for complex sections.

## Aha Moment

> Granularity isn't about "how much content" — it's about "how many independent checks of understanding." Each KP should correspond to one thing the student needs to verify they understood. If you can't think of a good verification question, the KP might not be a learnable unit.

## In-workflow Application

- `learning-item-granularity/SKILL.md`: Granularity rules
- `gates/learning-item-granularity-gate.md`: Enforces limits
- `knowledge-points.md`: Each row is one KP at the right granularity
