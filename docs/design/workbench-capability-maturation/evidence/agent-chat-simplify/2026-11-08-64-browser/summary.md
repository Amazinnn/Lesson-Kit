# agent-chat-simplify 6.4 真实浏览器验收（2026-11-08）

## 环境与身份

- 仓库：`D:\Projects\Academic Workflow\lesson-kit`，分支 `main`（工作区含本会话 6.4 修复前改动）。
- daemon：`http://127.0.0.1:3123`，`/api/runtime` 核对 `source_root = D:\Projects\Academic Workflow\lesson-kit`（本会话纠正了 editable 安装：此前 `.pth` 实际指向 `D:\.codex\worktrees\course-sync\lesson-kit`，已 `pip install -e . --no-deps` 重装回主检出；此前"editable=主检出"的记录是 cwd 污染的误判）。
- 隔离：`LESSONKIT_WB_HOME=%TEMP%\wb64\home`，临时工作区 `wb64`（fixture 库：1 知识点 + 15 题），卷 `ps-001`（14 题）由真实 CLI `lesson-kit papers wb64 save` 创建。真实注册表与 22 个真实工作区零接触，未写任何真实学习记录。

## Provider 桩边界（诚实声明）

- provider `pi` 由 `tests/workbench/fake_pi_rpc.py` 派生的协议忠实假体（`%TEMP%\wb64\fake_pi_browser.py`）承担：同一 pi RPC JSONL 协议，turn 1 输出 3360 字符工具结果 + `paper_update_proposal` 动作块。
- **真实链路**：bridge 动作解析、pending approval 预览/落盘、批准应用（`practice_sets.update_saved` 真实改卷）、HTTP 全部为生产代码；**桩**：仅 LLM 子进程。node 契约已钉卡片数据面，本验收补浏览器布局面。
- 前置 1（推送）已完成：`3dca0cc0..b6881510` 已推送 origin/main（所有者本轮明示授权）。

## 8 项清单（全部本会话浏览器实测，Playwright）

| # | 项目 | 证据 | 结果 |
|---|---|---|---|
| 1 | Enter 发送 | 真实 `POST /ai/sessions/conv-001/turns` → 200，turn-001 跑完，气泡出现、输入框清空 | PASS |
| 2 | Ctrl+Enter 发送 | turn-002 真实 POST → 200，批准后空队列直发 | PASS |
| 3 | Shift+Enter 换行不发送 | 原生键盘：值变为 `"第一行验收\n"`，user 气泡数不变（2） | PASS |
| 4 | 满宽输入框 | input 269px 贴满 339px 行（行内其余为发送按钮），与 2026-11-01 实测比例一致 | PASS |
| 5 | 无影响行/退役件 | `.ai-plan-impact`=0、`.ai-side-label`=0、`.ai-chip`=0；`#ai-handoff-status` 仍在但为 stop-wait 功能指示（常态 empty+`hidden`+`display:none`，node 测试 964/1052 钉住该功能语义） | PASS |
| 6 | 审批单卡 | pending 仅 composer 一处（643px 详情折叠态）；批准后 panel 隐藏、历史决议卡 1 张（"已批准"）；批准真实落盘（ps-001 题序反转确认） | PASS |
| 7 | 空队列审批后直发 | 批准决议后队列保持空、无出站行，turn-002 直发 | PASS |
| 8 | 三类长卡折叠/展开 | 工具输出 2590px↔320px；审批详情 643px↔638px 展开；恢复卡 690px↔320px；三卡 `aria-expanded` 双向翻转、"展开完整内容/收起" aria-label 正确 | PASS（含一处真缺陷修复，见下） |

`#ai-status` 可见性：常驻布局内（`offsetParent` 非空），发送失败时如实显示"发送失败：Failed to fetch"。

## 本轮发现并修复的缺陷（workbench.js）

恢复卡 690px 却不折叠：`wbApplyCollapse(card, true)` 在 `recoveryList.appendChild(card)` **之前**调用——卡片未入 DOM，`scrollHeight=0` 永远低于 320px 阈值。同类：排队编辑恢复卡（editCard）完全没有挂折叠。修复 = 调整两处顺序/补挂（`workbench.js` aiRenderOutbox），node 套件无法测出（jsdom 无布局），浏览器验收为该行为的唯一钉法。

- 回归：`pytest tests -k "conversation or agent_session or ui"` 312 passed；node 套件注册 12 passed；两个 node 会话/交互套件 0 fail。
- 修复后浏览器复验：恢复卡折叠/展开全对（690↔320px，aria 翻转）。

## 未运行（如实）

- 真实 LLM provider 轮次（免费 deepseek 走 pi CLI）：本验收用协议忠实假体；真实 provider 行为差异不在 6.4 清单内。
- 真实触控设备；waiting-for-stop 中断交接的浏览器走查（属 ai-teacher-bridge 规格场景，非 6.4 清单项）。
- 恢复卡"重新发送/恢复原文"按钮业务流（outbox 重试语义由 node/pytest 钉住）。
