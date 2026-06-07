# Gate: Style and Tone

Use this gate before exporting any 速览 (formerly 首读教案) file.

Check that the final artifact meets the "一针见血" (direct and concise) language standard and contains no workflow terminology.

| Failure | Return to | Forbidden repair |
|---------|-----------|-----------------|
| Final artifact contains workflow terminology: 首读, 回看, 先确认, 不要急着, 这里的阅读重点是, 记住, or similar process-oriented language | `first-pass-structure-plan.md` and final artifact | Search-and-replace removal of individual terms without rewriting the surrounding prose |
| A knowledge block reads like a one-sentence summary or explanation rather than a definition plus through-line accent | `intermediate/first_pass/02_analysis/knowledge-relationship-analysis.md` and `first-pass-structure-plan.md` | Adding "回看" or "首读时" to a summary sentence to make it sound like a reading guide |
| Knowledge block prose explains the source content as a substitute for reading | `intermediate/first_pass/02_analysis/knowledge-points.md` and final artifact | Renaming "explanation" as "reading guide" without changing the content |
| MCQ options lack differentiation (options too similar, or no plausible distractor) | `first-pass-structure-plan.md` | Making options shorter without adding real distinctions |
| MCQ stem embeds information that belongs in options | `first-pass-structure-plan.md` | Moving stem info to options without adjusting the question design |
| Chapter-end summary reads like a mechanical list rather than a coherent overview | `first-pass-structure-plan.md` | Adding transition words without restructuring |
| Final artifact contains internal fields (kp_id, knowledge_type, writing_view, rendering_intent, question_target, template labels) | `first-pass-structure-plan.md` | Removing field labels while keeping the structural format of internal fields |

Pass only when every knowledge block can be read as an independent piece of knowledge organization — not a workflow instruction, not a summary, and not an exam-prep guide.
