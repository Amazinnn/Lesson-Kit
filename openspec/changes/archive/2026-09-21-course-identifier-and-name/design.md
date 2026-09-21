# design — course-identifier-and-name

## 上下文

- 现有推导（上一轮 `init-ergonomics-and-cjk-names` 落地）：显式 `--course` ›
  已成型池的文件名 › ASCII 文件夹名折叠；**非 ASCII 文件夹名报错**并打印可粘贴命令
  （`cli/main.py` 的 `_init_course`）。
- 课程串同时是：内容 id 前缀（`<course>-<chapter>-kb-001`）、池文件名
  （`pool/<course>.db`）、figures/output 的目录名。
- 硬约束（上一轮实测）：workbench 门禁的 id 正则只收小写 ASCII；`pipeline/` 的
  id 校验同样只收 ASCII 且被 AGENTS.md 列为禁改契约。所以"标识符"必须保持 ASCII。
- 工作区名本来就自由（默认文件夹名，中文可用，hub 与顶栏显示的就是它）。

## Goals / Non-Goals

**Goals**

- 任何文件夹零参 `init` 成功；名字随意；标识符自动且可预测。
- 显式 `--course`/`use <course>` 的非法值当场报错，不再埋进注册表。

**Non-Goals**

- 不允许中文当标识符（放开字符集需要动 `pipeline/` 契约，不在本次）。
- 不改 id 格式、不迁移既有 `dmath` 数据、不改池结构。
- 不引入交互式提问。

## 决策

### 一、标识符来源次序加"顺序短码"

`--course` › 池文件名 › ASCII 文件夹名 › **`c01`/`c02`…**。
短码 = 「注册表中所有 `active_course` 匹配 `c(\d+)` 的最大值」与「本文件夹
`pool/c*.db`」取并，+1 后两位补零。扫描注册表使得连续新建的 kit 依次得
`c01`、`c02`…（所有者预期的"顺序"）；没有新持久字段，注册表丢了大不了重新从
`c01` 开始（短码只在建池那一刻需要，之后由池文件名与 id 自证）。

### 二、显式 `--course` / `use` 的 course 必须过 slug 校验

沿用同一个 `COURSE_SLUG` 正则；拒绝时说明理由（"它是每一条内容 id 的前缀"）。
此前无校验，`--course 大学物理` 会写进注册表并生成永远过不了门禁的 id。

### 三、顶栏只显示名字（+ 章）

`pages.shell` 里 `course` 仅用于 meta 行（`:37/40/41`）；改为名字 + 有章时的章。
机器短码退到不可见处（池文件名、id、`ls`/`doctor` 等数据面仍可见——那是调试需要）。

### 四、ASCII 文件夹名的推导保留

`Linear Algebra (Spring)` → `linear-algebra-spring`：能免费拿到可读 id 就别浪费。
只有推不出来时才落到短码——即"能推导就推导"的既有原则。

## Risks / Trade-offs

- 短码与课程名无关（`c01` 看不出是物理还是化学）：可读性靠工作区名承担；若日后
  想要现成的可读 id，可在建池后手工改池名与 id 前缀（本轮不做）。
- 两个 kit 各自从 `c01` 起并不冲突（id 唯一性只需在池内成立）；注册表扫描只是让
  同一台机器上的顺序更好看。
- 顶栏去掉课程标识符后，"我到底在看哪个池"少了一个线索；由工作区名 + 池文件名
  承担，`lesson-kit ls` 仍列出 course/chapter。
