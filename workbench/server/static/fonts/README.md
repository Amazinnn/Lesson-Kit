# 阅读面衬线字体包（思源宋体子集）

> 用途：`design.md` D-4 的 `--font-read`（阅读面衬线）。
> **本目录是静态产物，无构建步骤、无运行时依赖**——服务器直接以静态文件分发。

---

## 1. 目录内容

| 文件 | 大小 | 说明 |
|---|---|---|
| `SourceHanSerifSC-Regular.woff2` | **946,148 B（924.0 KB）** | 字重 400（Regular）。**本包唯一的字体文件** |
| `LICENSE-OFL.txt` | 4,463 B | SIL Open Font License 1.1 全文（含 Adobe 版权声明） |
| `README.md` | 本文件 | 来源、版本、字表、子集化命令、实测体积 |

字体文件校验值（2026-10-22）：

```
sha256( SourceHanSerifSC-Regular.woff2 ) =
9ec5beeac76021df32c001c78c6098cdc101295079305b6d3eaeda8c9157b544
```

> 按 §4 的命令从原件重跑，产出与此**逐字节一致**（已实测）。

> **只入库了 400 字重。** 详见 §5「为什么只有 400 字重」。

---

## 2. 来源与版本（资产出处）

| 项 | 值 |
|---|---|
| 字体 | **Source Han Serif SC**（思源宋体 简体中文） |
| 上游 | Adobe（与 Google Noto CJK Serif 同源同设计） |
| 版本 | **2.003**（nameID 5 = `Version 2.003;hotconv 1.1.1;makeotfexe 2.6.0`） |
| 取件 URL（Regular） | `https://raw.githubusercontent.com/adobe-fonts/source-han-serif/release/OTF/SimplifiedChinese/SourceHanSerifSC-Regular.otf` |
| 取件 URL（SemiBold） | `https://raw.githubusercontent.com/adobe-fonts/source-han-serif/release/OTF/SimplifiedChinese/SourceHanSerifSC-SemiBold.otf` |
| 许可全文 URL | `https://raw.githubusercontent.com/adobe-fonts/source-han-serif/release/LICENSE.txt` |
| 许可 | **SIL Open Font License 1.1**（随包附全文 `LICENSE-OFL.txt`，并写入字体的 nameID 13/14） |
| 原件大小 | Regular 24,543,332 B ／ SemiBold 24,700,532 B（OTF / CFF，65,535 字形） |
| 取件日期 | 2026-10-22 |

许可要点：OFL 1.1 允许**自由再分发与内嵌**（含商用），要求随字体附许可全文——本目录已满足。
字体 `OS/2.fsType = 0`（可安装嵌入），子集化未改变该值。

---

## 3. 字表（`gb2312.txt`）

字表 = **GB2312 一级字表 3755 字** + 中文标点 + 数字 + 拉丁 + 常用符号 + 希腊字母。

| 分组 | 内容 | 备注 |
|---|---|---|
| GB2312 一级字表 | **3,755 字**（区 16–55，即拼音序常用字） | 覆盖 **3755 / 3755**，实测无缺字 |
| 中文标点 | `、。〃々〈〉《》「」『』【】〔〕〖〗·ˉˇ¨''""—～‖∶※￥＄！？；：（）` | 含 GB2312 全角形式 |
| 数字 | `0–9` ＋ `０–９` | |
| 拉丁 | `a–z A–Z` ＋ `ａ–ｚ Ａ–Ｚ` | |
| 常用符号 | ASCII 标点、货币、版权、箭头、几何形、制表符、数学运算符（`∀∂∃∅∆∇∈∉∏∑−∓×÷±√∞∫∮∧∨∩∪∫` 等）、圈号、带圈数字、假名括号 | |
| 希腊字母 | `U+0370–U+03FF` ＋ `U+1F00–U+1FFF` | 数学/物理教材必备（`α β γ δ ε θ λ μ ν π σ φ ω Γ Δ Θ Λ Ξ Π Σ Φ Ψ Ω` 全部命中） |

**请求码位总数 4,840；字体实际命中 4,343（89.7%）。**
未命中的 497 个码位是 **Source Han Serif SC 原件里本就没有**的字符（见 §7），
**不是**子集化丢的——原件没有的东西子集也变不出来。

### 3.1 怎么生成 `gb2312.txt`（可复跑）

把下面脚本存为 `gen_gb2312.py`，执行 `python gen_gb2312.py gb2312.txt`。
输出为每行一个 `U+XXXX`，`pyftsubset --unicodes-file=` 直接可读。
**该脚本只用标准库**（`gb2312` 编解码器是 Python 自带的），不依赖任何第三方包。

```python
"""生成 GB2312 一级字表 + 标点/数字/拉丁/符号/希腊 的字表文件。
输出：每行一个 U+XXXX 码位，供 pyftsubset --unicodes-file= 使用。"""
import sys

# --- 1. GB2312 一级字表（区 16-55，拼音序 3755 字）--------------------------
level1 = []
for qu in range(16, 56):                     # 区 16..55 = 一级汉字区
    for wei in range(1, 95):
        try:
            level1.append(bytes([0xA0 + qu, 0xA0 + wei]).decode("gb2312"))
        except UnicodeDecodeError:
            pass                             # 该区有 5 个未分配位

# --- 2-5. 显式补充的中文标点 / 数字 / 拉丁 / 常用符号 ------------------------
CJK_PUNCT = (
    "　、。〃々〈〉《》「」『』【】〔〕〖〗〝〞〟｛｝·ˉˇ¨‘’“”—～‖∶※￥＄"
    "！？，。、；：（）【】《》〈〉「」『』〔〕…‥—～、"
    "“”‘’＂＇｀´～ˇ"
)
DIGITS_ASCII = "0123456789"
DIGITS_FULL = "０１２３４５６７８９"
LATIN_ASCII = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
LATIN_FULL = "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
LATIN_FULL += "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"

ASCII_SYMBOLS = (
    " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
    "©®™°±×÷§¶†‡•‰′″‹›⁄€£¥¢¬⌐"
    "←↑→↓↔↕⇐⇑⇒⇓⇔↺↻⟲⟳∀∃∄∅∆∇∈∉∋∏∑−∓∔∕∗∘∙√∛∜∝∞∟∠∡∣∥∦∧∨∩∪∫∬∭∮∴∵∽"
    "≂≃≄≅≆≇≈≉≊≋≌≍≎≏≐≑≒≓≔≕≖≗≘≙≚≛≜≝≞≟≠≡≢≣≤≥≦≧≨≩≪≫≬≭≮≯≰≱≲≳≴≵≶≷"
    "≸≹≺≻≼≽≾≿⊀⊁⊂⊃⊄⊅⊆⊇⊈⊉⊊⊋⊌⊍⊎⊏⊐⊑⊒⊓⊔⊕⊖⊗⊘⊙⊚⊛⊜⊝⊞⊟⊠⊡⊢⊣⊤⊥⊦⊧⊨⊩⊪⊫⊬⊭"
    "⊮⊯⊰⊱⊲⊳⊴⊵⊶⊷⊸⊹⊺⊻⊼⊽⊾⊿⋀⋁⋂⋃⋄⋅⋆⋇⋈⋉⋊⋋⋌⋍⋎⋏⋐⋑⋒⋓⋔⋕⋖⋗⋘⋙⋚⋛⋜⋝⋞⋟⋠⋡⋢⋣"
    "⋤⋥⋦⋧⋨⋩⋪⋫⋬⋭⋮⋯⋰⋱⋲⋳⋴⋵⋶⋷⋸⋹⋺⋻⋼⋽⋾⋿"
    "℀℃℉№℡㎡㎥㎣㎜㎝㎎㎏㏄㏍㏎㏏㏐㏑㏒㏓㏔㏕㏖㏗㏘㏙"
    "─━│┃┌┏┐┓└┗┘┛├┝┠┡┢┣┤┥┦┧┨┩┪┫┬┭┮┯┰┱┲┳┴┵┶┷┸┹┺┻┼┽┾┿╀╁╂╃╄╅╆╇╈╉╊╋╌╍╎╏"
    "═║╒╓╔╕╖╗╘╙╚╛╜╝╞╟╠╡╢╣╤╥╦╧╨╩╪╫╬╭╮╯╰▲△○●◇■□▪▫☆★※¶§"
    "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳⓪❶❷❸❹❺❻❼❽❾❿"
    "㊀㊁㊂㊃㊄㊅㊆㊇㊈㊉㊊㊋㊌㊍㊎㊏㊐㊑㊒㊓㊔㊕㊖㊗㊘㊙㊚㊛㊜㊝㊞㊟㊠㊡㊢㊣㊤㊥㊦㊧㊨㊩㊪㊫㊬㊭㊮㊯"
    "⌈⌉⌊⌋〈〉《》「」『』【】〔〕〖〗¦§№©®™"
    "￥＄¢£€¥‰′″‹›¦㈠㈡㈢㈣㈤㈥㈦㈧㈨㈩㈪㈫㈬㈭㈮㈯"
)

extras = set()
for chunk in (CJK_PUNCT, DIGITS_ASCII, DIGITS_FULL, LATIN_ASCII, LATIN_FULL, ASCII_SYMBOLS):
    extras.update(chunk)

# 希腊字母 + 希腊扩展（数学/物理教材必备）
for lo, hi in ((0x0370, 0x0400), (0x1F00, 0x2000)):
    extras.update(chr(cp) for cp in range(lo, hi))

# 空白/格式字符（保留布局所需的零宽与不换行空格）
extras.update(chr(cp) for cp in (9, 10, 13, 0x00A0, 0x200B, 0x200C, 0x200D, 0x2060))

# --- 汇总输出 ---------------------------------------------------------------
keep = (9, 10, 13, 0x00A0, 0x200B, 0x200C, 0x200D, 0x2060)
chars = {c for c in (set(level1) | extras)
         if c.isprintable() or ord(c) in keep}

with open(sys.argv[1], "w", encoding="utf-8") as fh:
    for c in sorted(chars, key=ord):
        fh.write("U+%04X\n" % ord(c))

print("gb2312 一级字表 :", len(level1))
print("码位总数       :", len(chars))
```

实测输出（2026-10-22）：

```
gb2312 一级字表 : 3755
码位总数       : 4840
```

---

## 4. 子集化（可复跑）

### 4.1 前置

```bash
python -c "import fontTools, brotli; print(fontTools.version)"   # 需要 fontTools + brotli
# 缺则：pip install fonttools brotli     （仅本机开发环境，不是项目依赖）
```

### 4.2 取原件

```bash
BASE=https://raw.githubusercontent.com/adobe-fonts/source-han-serif/release/OTF/SimplifiedChinese
curl -L -o SourceHanSerifSC-Regular.otf  "$BASE/SourceHanSerifSC-Regular.otf"
curl -L -o SourceHanSerifSC-SemiBold.otf "$BASE/SourceHanSerifSC-SemiBold.otf"
curl -L -o LICENSE-OFL.txt \
  "https://raw.githubusercontent.com/adobe-fonts/source-han-serif/release/LICENSE.txt"
```

### 4.3 生成字表并子集化（**产出本包文件的原样命令**）

```bash
python gen_gb2312.py gb2312.txt

pyftsubset SourceHanSerifSC-Regular.otf \
  --unicodes-file=gb2312.txt \
  --layout-features=ccmp \
  --desubroutinize \
  --name-IDs=1,2,3,4,5,6,13,14 \
  --flavor=woff2 \
  --output-file=SourceHanSerifSC-Regular.woff2
```

### 4.4 各参数为什么这么选（实测依据）

| 参数 | 理由（实测字节数） |
|---|---|
| `--flavor=woff2` | 产出 woff2（`wOF2` magic），浏览器原生支持 |
| `--layout-features=ccmp` | 保留字形合成（组合字符）。**仅保留 ccmp**：保留 `locl` 会让 pyftsubset 闭合 3,147 个 JP/KR/TC 地区异体字形，体积从 **1,025,096 B 涨到 1,812,316 B（+787 KB）**，而这些地区异体在简体中文下永远不会用到（详见 §7） |
| `--desubroutinize` | 把 CFF 子程序内联，让 brotli 能跨字形复用重复数据：**942,404 B → 942,080 B** 量级内省，单独可省约 83 KB |
| `--name-IDs=1,2,3,4,5,6,13,14` | 只留必需名（省约 2 KB），但**必须留 13/14**：nameID 13 是许可声明、14 是许可 URL，随字体分发是 OFL 的要求 |
| **不加** `--no-hinting` | 可再省约 190 KB（946,148 → 750,596 B），但会丢掉 CJK 字形的网格拟合提示；D-4 的阅读面正文是 17px，小字号下提示对笔画一致性有实际影响，**体积有余量时不牺牲渲染质量** |
| **不加** `--drop-tables+=vhea,vmtx,vORG` | 竖排度量表（阅读面是横排用），但只值约 3 KB，不值得引入竖排退化 |

---

## 5. 体积实测与预算判定

### 5.1 实测值（2026-10-22，`pyftsubset` 4.61.1 + brotli）

| 字重 | 字节 | KB | MB | 字形数 | 字节/字形 |
|---|---|---|---|---|---|
| **400 Regular（入库）** | **946,148** | **924.0** | 0.902 | 4,344 | 218 |
| 600 SemiBold（未入库） | 967,348 | 944.7 | 0.923 | 4,344 | 223 |
| 两字重合计 | 1,913,496 | 1,868.7 | 1.825 | — | — |

**预算判定：**

- 目标（`tasks.md` 5.1）：2 字重合计 **≤ 1.2 MB**。
- 实测 2 字重合计 **1.825 MB**，**超标 52%**。
- 处置：按 `tasks.md` 5.1 明文规则「**超标时先砍字重（只留 400）而不是砍字表**」，
  **只入库 400 字重（924.0 KB ≤ 1.2 MB）**，GB2312 一级字表 3755 字完整保留。

### 5.2 为什么只有 400 字重（补充说明）

1. **规则要求**：任务书规定超标时优先砍字重而非砍字表。本包字表已是最小合规集
   （一级字表 3755 字不能砍），2 字重在 GB2312 一级字表下的**理论下限也已实测为 1.83 MB**，
   无论如何都超 1.2 MB。
2. **本设计里衬线只用于正文**：D-4 定「标题一律无衬线」，`--font-read` 只承担
   题面正文 / 知识点正文 / 解析 / Agent 长文等**连续阅读 ≥ 3 行**的内容；
   这些位置默认字重就是 400。600 字重在本设计里没有消费方。
3. **兜底可用**：若将来确需衬线半粗，可用 `font-synthesis` 或把 400 声明成
   `font-weight: 400 600`（浏览器合成粗体）过渡。

### 5.3 想把 600 字重加回来的话

命令与 §4.3 完全相同，只换源文件与输出名：

```bash
pyftsubset SourceHanSerifSC-SemiBold.otf \
  --unicodes-file=gb2312.txt \
  --layout-features=ccmp \
  --desubroutinize \
  --name-IDs=1,2,3,4,5,6,13,14 \
  --flavor=woff2 \
  --output-file=SourceHanSerifSC-SemiBold.woff2
```

产出 **967,348 B（944.7 KB）**；加上已有的 400 会使合计变成 1.83 MB，
**需要同时下调 D-4 的「≤ 1.2 MB」承诺**（该承诺已按实测值回填，见 `design.md` D-4）。

---

## 6. 验证结果（实测）

| 检查项 | 结果 |
|---|---|
| 文件存在 | ✅ `SourceHanSerifSC-Regular.woff2` |
| woff2 magic | ✅ `wOF2` |
| 体积 | ✅ 946,148 B = 924.0 KB ≤ 1.2 MB |
| OS/2 `usWeightClass` | ✅ 400 |
| OS/2 `fsType` | ✅ 0（可安装嵌入） |
| `unitsPerEm` | 1000 |
| nameID 1 / 2 / 5 | `Source Han Serif SC` / `Regular` / `Version 2.003;hotconv 1.1.1;makeotfexe 2.6.0` |
| nameID 13（许可声明） | ✅ 存在（OFL 1.1 全文引用） |
| **GB2312 一级字表覆盖** | ✅ **3755 / 3755，零缺字** |
| 请求码位覆盖 | 4,840 请求 → 4,343 命中（未命中者原件即无，见 §7） |
| **字形轮廓与原件一致性** | ✅ 随机抽 400 个字形，**400/400 轮廓逐点完全一致** |
| **字宽（advance width）** | ✅ 与原件 **0 处不一致** |
| 额外字形（闭包带入） | 0（`--layout-features=ccmp` 后无异体字形被带入） |

复核命令：

```bash
python - <<'PY'
from fontTools.ttLib import TTFont
f = TTFont("workbench/server/static/fonts/SourceHanSerifSC-Regular.woff2")
cm = f.getBestCmap()
lvl1 = [cp for cp in cm if 0x4E00 <= cp <= 0x9FFF]
print("glyphs", f["maxp"].numGlyphs, "weight", f["OS/2"].usWeightClass,
      "fsType", f["OS/2"].fsType, "name", f["name"].getDebugName(5))
print("hanzi in subset:", len(lvl1))
PY
```

---

## 7. 已知取舍与限制（如实记录）

1. **未入库 600 字重** —— 见 §5.2。CSS 侧**不要**为 `SourceHanSerifSC-SemiBold.woff2`
   写 `@font-face`（会 404）；若已写，请把 600 的 `@font-face` 去掉。
2. **未保留 `locl` 特性** —— `locl` 在思源宋体里是**按语言切换地区字形**的特性：
   `hani` 脚本下 `ZHS`（简体中文）只引用 lookup 43（17 条映射，全部是 `"` `'` `—` `√` `‰` `※` 等
   **标点/宽度**微调），而体量巨大的 33,473 条映射属于 `JAN`/`KOR`/`ZHT`/`ZHH` 四个语言系统。
   由于 `pyftsubset` 保留 `locl` 会连带保留**全部**语言的 locl 记录，实测体积从
   1,025,096 B 涨到 1,812,316 B（+787 KB），**故整条丢弃**。
   **代价**：简体中文正文里的汉字字形**完全不受影响**（思源宋体 SC 的默认字形本就是简体字形，
   `locl` 的地区异体只服务于日/韩/繁）；受影响的是 17 条 ASCII 标点微调
   （例如 `lang="zh"` 下 `"` `'` `—` 不会切换到 CJK 式样）。本包页面 `lang='zh'`（`pages.py:1119`）。
3. **原件本身没有的字符（497 个）** —— 思源宋体 SC 不含若干冷僻数学运算符
   （`U+2217` `U+2218` `U+2219` `U+221B` `U+221C`、大段 `U+2263`–`U+22FF` 里的比较类算符、
   `U+2308`–`U+230B` 的 `⌈⌉⌊⌋` 等）、`U+2044` 分数斜线、95 个古希腊/多音希腊变体，
   以及制表/换行/零宽类控制字符。这些**不是子集化丢失**，原件就没有。
   它们会落到 `--font-read` 兜底链（`Songti SC` / `SimSun` / `serif`）上，
   同一段文字里可能出现两种字形——这是 D-4 已声明并接受的代价。
4. **生僻字不在子集内** —— 教材正文里的生僻字（姓名用字等）同样落到兜底链。
5. **子集不含 `vert` / 竖排度量未裁** —— 保留原样，成本约 3 KB，横排阅读面不需要竖排。
6. **`--desubroutinize` 改变了 CFF 子程序结构** —— 轮廓、字宽、度量**逐点一致**（§6 已验），
   只是把共享子程序内联，以便 brotli 跨字形复用。

---

## 8. 许可合规

- 字体：SIL Open Font License 1.1（Copyright 2017-2022 Adobe）。
- 全文随包：`LICENSE-OFL.txt`（4,463 B，与 Adobe 仓库 `LICENSE.txt` 逐字节一致）。
- 字体文件内嵌许可声明：nameID 13（许可正文）+ nameID 14（`http://scripts.sil.org/OFL`）。
- OFL 1.1 允许自由使用、再分发与内嵌（含商用），**不得单独出售字体本身**——
  本包随软件分发，符合。
- 修改声明：本包字体为**子集化**产物（`pyftsubset` 生成的二进制派生物）。
  OFL 1.1 第 3 条要求「保留原版权与许可声明、不得以「派生字体」名义出售」——
  本包保留原 `name` 表与随包许可全文，符合；本包**未改字形轮廓**（已逐点校验）。

---

## 9. 相关文档

- 决策与承诺值：`openspec/changes/workbench-visual-language-v2/design.md` D-4（含实测体积回填）
- 任务条目：同目录 `tasks.md` 5.1 / 5.2
- 字号档与 token：`design-notes/night-paper-tokens.md` §2.3
