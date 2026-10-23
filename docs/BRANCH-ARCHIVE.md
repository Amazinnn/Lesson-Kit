# 分支归档记录 — 2026-10-23

> **归档对象**：**已完全并入 `main`** 的本地分支 —— 成果在 `main` 里，
> 分支引用只是残留（本地 47 个分支，167 个含远端引用）。
>
> **归档方式（可恢复）**：**先打 `archive/<branch>` 附注 tag，再删分支与 worktree**
> ⇒ 一条命令即可复原：
>
> ```bash
> git branch <branch> archive/<branch>      # 复原分支
> git worktree add .worktrees/<name> <branch> # 需要工作目录时再补
> ```
>
> ⚠️ **远端引用（`origin/*`）一律不动** —— 那是远端状态，不是本地分支。
> ⚠️ **不 push、不合并 main**（所有者 2026-10-23 指示）。

## 保留的分支（未收工的工作，删了会丢独有提交）

| 分支 | 理由 |
|---|---|
| `main` | 主线 |
| `feat/workbench-visual-language-v2` | **当前分支**（视觉重做主线，含 V1 基线与四档几何） |
| 其余 17 个 | **还有独有的未合并提交**（`git branch --no-merged main`）—— 属未收工的工作，不是「残留」 |

## 已归档的分支（28 个）

| 分支 | 归档时的 tip | 日期 | 复原用 tag | 连带删掉的 worktree |
|---|---|---|---|---|
| `docs/free-paper-navigation` | `c1db449a` | 2026-10-19 | `archive/docs/free-paper-navigation` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/free-paper-navigation-design |
| `docs/paper-agent-contracts-20261017` | `351eeeb0` | 2026-10-17 | `archive/docs/paper-agent-contracts-20261017` | — |
| `docs/pool-pipeline-managed-paper` | `6b739e30` | 2026-10-15 | `archive/docs/pool-pipeline-managed-paper` | — |
| `feat/agent-paper-save` | `bf68c988` | 2026-10-14 | `archive/feat/agent-paper-save` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/urgent-dashboard-paper-20261014 |
| `feat/compact-agent-queue` | `a0303a6f` | 2026-10-21 | `archive/feat/compact-agent-queue` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/compact-agent-queue |
| `feat/hidden-course-layout` | `944b867c` | 2026-10-21 | `archive/feat/hidden-course-layout` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/hidden-course-layout |
| `feat/openspec-closeout-20261009` | `e6ea583e` | 2026-10-09 | `archive/feat/openspec-closeout-20261009` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/pr-closeout-20261009 |
| `feat/workbench-study-flow-graph` | `f83e0b56` | 2026-08-22 | `archive/feat/workbench-study-flow-graph` | — |
| `feature/problem-candidate-mvp` | `6cc1459a` | 2026-07-11 | `archive/feature/problem-candidate-mvp` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/problem-candidate-mvp |
| `fix/attempt-migration-references` | `1b253b53` | 2026-10-17 | `archive/fix/attempt-migration-references` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/repair-attempt-references |
| `fix/cli-bundled-skill` | `0c1b9ebd` | 2026-10-22 | `archive/fix/cli-bundled-skill` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/cli-bundled-skill |
| `fix/dashboard-paper-20261014` | `b5e0034c` | 2026-10-14 | `archive/fix/dashboard-paper-20261014` | — |
| `fix/graph-jitter` | `872e6777` | 2026-10-20 | `archive/fix/graph-jitter` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/graph-jitter |
| `fix/restore-topic-removal-20261010` | `2404f8f2` | 2026-10-10 | `archive/fix/restore-topic-removal-20261010` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/restore-topic-removal-20261010 |
| `review/governance-98-20261009` | `33bcf2e6` | 2026-10-09 | `archive/review/governance-98-20261009` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/governance-98-20261009 |
| `review/pr-audit-20261012` | `ea50586a` | 2026-10-14 | `archive/review/pr-audit-20261012` | — |
| `review/pr113-audit-20261012` | `ce480e90` | 2026-10-13 | `archive/review/pr113-audit-20261012` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/pr113-audit-20261012 |
| `review/pr114-audit-20261012` | `96a4a3a7` | 2026-10-12 | `archive/review/pr114-audit-20261012` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/pr114-audit-20261012 |
| `review/pr115-audit-20261012` | `79242754` | 2026-10-12 | `archive/review/pr115-audit-20261012` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/pr115-audit-20261012 |
| `review/pr116-audit-20261012` | `f84cd09d` | 2026-10-12 | `archive/review/pr116-audit-20261012` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/pr116-audit-20261012 |
| `review/pr117-audit-20261012` | `49cfa804` | 2026-10-12 | `archive/review/pr117-audit-20261012` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/pr117-audit-20261012 |
| `review/pr118-audit-20261012` | `b58d7695` | 2026-10-12 | `archive/review/pr118-audit-20261012` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/pr118-audit-20261012 |
| `review/pr119-audit-20261013` | `9b4e2666` | 2026-10-13 | `archive/review/pr119-audit-20261013` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/pr119-audit-20261013 |
| `review/pr120-audit-20261013` | `7256680d` | 2026-10-13 | `archive/review/pr120-audit-20261013` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/pr120-audit-20261013 |
| `review/pr121-audit-20261013` | `f103f3af` | 2026-10-13 | `archive/review/pr121-audit-20261013` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/pr121-audit-20261013 |
| `review/pr122-audit-20261013` | `cf63becb` | 2026-10-13 | `archive/review/pr122-audit-20261013` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/pr122-audit-20261013 |
| `review/pr123-audit-20261013` | `379de677` | 2026-10-13 | `archive/review/pr123-audit-20261013` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/pr123-audit-20261013 |
| `review/pr128` | `09d295f2` | 2026-10-15 | `archive/review/pr128` | D:/Projects/Academic Workflow/lesson-kit/.worktrees/pr-audit-20261012 |

## 校验

```bash
git tag -l 'archive/*' | wc -l      # 应等于归档条数
git branch --merged main --format='%(refname:short)'   # 归档后应只剩 main 与当前分支
```

⚠️ 若日后要复原**其中一个**分支，不要整批恢复 —— 按上面的 tag 单独取回即可。
