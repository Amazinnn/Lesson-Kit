# lesson-kit 知识池充实计划：dmath ch06 全 KP 覆盖 + 章级结构

**Context:** 真实教材 E2E 测试发现当前 dmath ch06 KP 池（22 KP）远少于用户已有的教案（765 行）。差距主要在方法级 KP、扩展定理、教学分类、节级 tagline、Mermaid 流程图。用户已确认：
- 全面加 KP（方法 + 扩展 + 经典恒等式）
- 节 tagline + Mermaid 作为 Markdown 正文一部分（**不**新建数据库表 / 字段）
- 表格用 Markdown 表格存 body

## 范围

### 1. KP 池充实（约 25 个新 KP，总计 47 个）

按用户教案的覆盖面，对当前 22 KP 进行扩展：

**§6.1 计数基础（新增 5 个）**
- 部分函数计数 (n+1)^m
- 圆排列 (n-1)!/2
- 反射等价 / 镜像 (n-1)!/2（n≥3）
- 布尔函数 / 子集对应 2^n
- 字段长度问题（bits → 2^t，octets → 2^8L）
- 英汉对照表（digit/character/bit 等 → 数学对象）→ 作为 KP 23 存放

**§6.2 鸽巢原理（新增 8 个）**
- 最小保证数定理：若要保证某盒子 ≥ r 个，最小对象数 k(r-1)+1
- 二分类加强结论：要么 a 个 A 要么 b 个 B（反证法）
- 前缀和鸽巢方法：连续区间和 → 序列两元素相等
- 整除链：奇数部分作为盒子
- 单调子序列定理：n²+1 个互异实数必有 n+1 单调子序列
- Ramsey R(3,3)=6 + 五人反例
- 0-and-1 倍数方法：1, 11, 111, ... 取 mod n
- 常见鸽巢模型表（生日/分数/同余等）→ 作为 KP 30 存放

**§6.3 排列与组合（新增 5 个）**
- 位串模型 + 至少/至多补集法
- Hockey-stick 恒等式
- 两阶段选取 C(n,r)·C(r,k) = C(n,k)·C(n-k, r-k)
- 组合证明方法（双计数 / 双射）
- 排列组合限制关键词表（all together/consecutive/no two adjacent 等）→ KP 存放

**§6.4 二项式（新增 3 个）**
- 指定项系数（线性 / 带幂 / 符号项）
- 进制展开 (11)_b^4 = (14641)_b
- 二项式定理代入基本恒等式表

**§6.5 广义（新增 4 个）**
- 重复组合变量视角（非负整数解）
- 下界替换 y_i = x_i - a_i
- 正整数解 C(N-1, m-1)
- 不等式 ≤ 引入辅助变量
- 球盒主表（可区分/不可区分 × 盒子类型 × 可空）→ KP 存放

**§6.6 生成（新增 0 个，保留现有 1 个）**

**总计：22 + 25 ≈ 47 KP**（含 4-5 个表格类 KP 存 body Markdown 表格）

### 2. 节 tagline 集成到 H4 标题

**方案：** print-graph.py 当前 H4 标题是 `#### §X-Y`。改为 `#### §X-Y {section_tagline}`。

section_tagline 来源：用户教案已经定义了：
- §6.1 → "计数基础：先确定对象、步骤与是否重复"
- §6.2 → "鸽巢原理：把存在性问题变成盒子容量问题"
- §6.3 → "排列与组合：有序、无序与限制条件的翻译"
- §6.4 → "二项式系数与恒等式：把选择问题写成代数系数"
- §6.5 → "广义排列与组合：重复、不可区分、球盒与多项式系数"
- §6.6 → "生成排列与组合：从计数公式到列举算法"

**数据流：** 在 `intermediate/dmath/extraction/ch06/02_analysis/section_taglines.json` 存映射表（不在 SQL 里）。print-graph.py 读这个表拼到 H4 标题后面。

```json
{
  "§6.1": "计数基础：先确定对象、步骤与是否重复",
  "§6.2": "鸽巢原理：把存在性问题变成盒子容量问题",
  ...
}
```

### 3. 章级 Mermaid 流程图

**方案：** print-graph.py 在 H1 标题之后渲染 Mermaid 块。流程图内容从用户教案第 5-17 行原样搬过来。

**数据流：** 在 `intermediate/dmath/extraction/ch06/02_analysis/chapter_diagram.mmd` 存 Mermaid 源码。print-graph.py 读这个文件，嵌在 H1 之后、第一个 H4 之前。

### 4. print-graph.py 改动

- 新增读 `section_taglines.json` 和 `chapter_diagram.mmd` 的逻辑
- H4 标题拼接 tagline
- 章首插入 ```mermaid fenced code block```
- 保持现有叙述型结构（无 wiki link，2 个空行间隔）

## 文件清单

| 路径 | 动作 |
|---|---|
| `intermediate/dmath/extraction/ch06/02_analysis/pool-insert-manifest.json` | 修改：22 KP → ~47 KP（新增 25 个）|
| `intermediate/dmath/extraction/ch06/02_analysis/section_taglines.json` | **新建**：节标签表 |
| `intermediate/dmath/extraction/ch06/02_analysis/chapter_diagram.mmd` | **新建**：章级 Mermaid 流程图 |
| `pool/scripts/print-graph.py` | 修改：读 tagline + diagram，渲染 H4 + Mermaid 块 |
| `docs/design/print-graph-design.md` | 修改：新增 "section tagline + chapter diagram" 章节 |

## 验证

```bash
# 1. 重跑 create + insert + validate
python pipeline/scripts/create-tables.py --db pool/dmath.db --force
python pipeline/scripts/insert-knowledge-points.py --db pool/dmath.db --manifest intermediate/dmath/extraction/ch06/02_analysis/pool-insert-manifest.json --upsert
python pipeline/scripts/validate-pool.py --db pool/dmath.db --chapter ch06 --course dmath  # PASS, 0 ERROR

# 2. 重跑 print
rm -rf output/dmath && mkdir -p output/dmath/ch06
python pool/scripts/print-graph.py --db pool/dmath.db --course dmath --chapter ch06 --course-name "Discrete Mathematics" --out output/dmath/ch06/

# 3. 检查
# - 47 KP 全部入库
# - H4 标题带 tagline (e.g. "#### §6.1 计数基础：先确定对象、步骤与是否重复")
# - 章首有 ```mermaid ... ``` 块
# - 输出行数约 500+（vs 当前 225）
# - grep "[[" 期望 0（无 wiki link）
```

## 不在范围内

- 课后习题池（用户已推迟）
- 跨章交叉链接
- 章节内独立的 method-KP 视图
- 教学卡片视图（"方法卡片""考点速览"等）— 后续可基于 knowledge_type 字段做
- 知识图谱（Mermaid 流程图已经涵盖章内流程，跨章网络是未来范围）

## 后续（不阻塞 MVP）

- knowledge_type 枚举扩展（theorem / method / classification / counter-example / worked-example）以便视图层分组
- 每节独立文件 vs 单章文件模式（目前单章）
- 章级 Mermaid 用 Vue/Mermaid 渲染（现在直接嵌 Markdown fenced block）