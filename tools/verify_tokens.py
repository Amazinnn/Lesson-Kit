#!/usr/bin/env python3
"""对比度复测 + 夜纸值集核对（workbench-visual-language-v2 · tasks.md 12.1 / 12.3）。

用法
----
    python tools/verify_tokens.py [workbench/server/static/workbench.css]

不带参数时默认用**仓库内**的那份 `workbench/server/static/workbench.css`。
输出两段：

  ① 值集核对（12.1）：把 CSS 里 `:root` 与 `html[data-theme="night"]` 两套值 token
     逐项与权威表对照 —— 权威表 = openspec/changes/workbench-visual-language-v2/
     design-notes/night-paper-tokens.md §3（52 个值 token）。
  ② 对比度复测表（12.3）：把 43 组配对用 **CSS 里的实际取值** 重算一遍，
     两主题各出一行。

**退出码**
    0  全部适用配对都达标
    1  存在**低于判定线**的配对（便于将来接进 CI 闸门）
    2  脚本自身出错（CSS 解析不出取值 / 缺 token）

判定线（权威表 §4.1）：正文/次要文字 ≥ 4.5:1 · 三级文字与控件边界/非文本 ≥ 3:1 ·
大字号 ≥ 3:1。

纯标准库（WCAG 2.x 相对亮度公式），无第三方依赖。
"""
import os
import re
import sys

# --------------------------------------------------------------------------
# 权威值表（night-paper-tokens.md §3，52 个值 token）：浅色 / 夜纸
# --------------------------------------------------------------------------
AUTH = {
    # §3.1 纸面层级 (6)
    "--surface-base":   ("#fdf8ef", "#1c1a16"),
    "--surface-card":   ("#fffdf7", "#232019"),
    "--surface-raised": ("#ffffff", "#2b2620"),
    "--surface-sunken": ("#f2ece1", "#272319"),
    "--surface-code":   ("#221f1a", "#14120f"),
    "--surface-sheet":  ("#fffdf7", "#1c1a16"),
    # §3.2 墨与文字 (8)
    "--ink-strong":   ("#221f1a", "#f4ede0"),
    "--ink-body":     ("#3b3630", "#e7dfd0"),
    "--ink-muted":    ("#6b6459", "#c2b8a5"),
    "--ink-faint":    ("#8d8578", "#978d7c"),
    "--ink-disabled": ("#8a8275", "#7a7162"),
    "--ink-on-role":  ("#fffdf7", "#14120f"),
    "--ink-on-warm":  ("#221f1a", "#14120f"),
    "--ink-inverse":  ("#fffdf7", "#f4ede0"),
    # §3.3 规则线 (3)
    "--rule-hair":      ("#e6dcc4", "#332d25"),
    "--rule-control":   ("#847552", "#7d7361"),
    "--rule-structure": ("#221f1a", "#ece3d3"),
    # §3.4 角色色 (11)
    "--role-blue":       ("#2b62e8", "#7291de"),
    "--role-blue-press": ("#1f4fc4", "#8fa9e8"),
    "--role-blue-wash":  ("#f2f0ef", "#292929"),
    "--role-blue-soft":  ("#e0e3ee", "#31343c"),
    "--role-yellow":       ("#f5c518", "#e0c151"),
    "--role-yellow-deep":  ("#8a6a00", "#f0d98a"),
    "--role-yellow-soft":  ("#fcf0cd", "#3d3721"),
    "--role-red":       ("#d1392b", "#d4736b"),
    "--role-red-ink":   ("#b8331f", "#e08878"),
    "--role-red-wash":  ("#f9e9df", "#352821"),
    "--role-red-soft":  ("#f6d9d0", "#432f28"),
    # §3.5 交互面纱 (3)
    "--veil-hover":  ("rgb(61 52 37 / 6%)",  "rgb(255 244 224 / 6%)"),
    "--veil-active": ("rgb(61 52 37 / 11%)", "rgb(255 244 224 / 12%)"),
    "--veil-modal":  ("rgb(33 31 26 / 42%)", "rgb(20 18 15 / 58%)"),
    # §3.6 抬升 / 阴影 (3) —— 多重阴影，按字符串比
    "--elev-1": (
        "0 1px 2px rgb(61 52 37 / 6%), 0 4px 12px rgb(61 52 37 / 4%)",
        "0 1px 2px rgb(0 0 0 / 30%), inset 0 1px 0 rgb(255 238 210 / 5%)",
    ),
    "--elev-2": (
        "0 2px 6px rgb(61 52 37 / 8%), 0 12px 28px rgb(61 52 37 / 8%)",
        "0 10px 28px rgb(0 0 0 / 38%), 0 0 24px rgb(255 236 200 / 5%),"
        " inset 0 1px 0 rgb(255 238 210 / 7%)",
    ),
    "--elev-3": (
        "0 4px 12px rgb(61 52 37 / 10%), 0 20px 48px rgb(61 52 37 / 12%)",
        "0 20px 48px rgb(0 0 0 / 52%), 0 0 32px rgb(255 236 200 / 6%),"
        " inset 0 1px 0 rgb(255 238 210 / 9%)",
    ),
    # §3.7 焦点 (5)
    "--focus-outer": ("#2b62e8", "#9dbcff"),
    "--focus-inner": ("#fffdf7", "#14120f"),
    "--focus-width": ("2px", "2px"),
    "--focus-offset": ("2px", "2px"),
    "--focus-halo": ("0 0 0 4px rgb(43 98 232 / 18%)",
                    "0 0 0 4px rgb(157 188 255 / 20%)"),
    # §3.8 骨架屏 (2)
    "--skeleton-base":  ("#ece3cf", "#26221b"),
    "--skeleton-sheen": ("#fdf8ef", "#3c3529"),
    # §3.9 插画与图案 (6)
    "--art-ink":     ("#2a2620", "#e6ddcd"),
    "--art-paper":   ("#fffdf7", "#232019"),
    "--art-wash-blue":   ("#e1e7f5", "#303239"),
    "--art-wash-yellow": ("#fdf3cf", "#3d3721"),
    "--art-wash-red":    ("#f9e5df", "#3c2c24"),
    "--art-highlight":   ("rgb(255 255 255 / 55%)", "rgb(255 240 214 / 8%)"),
    # §3.10 数据层热力 (4)
    "--heat-1": ("#d0dcfa", "#31343c"),
    "--heat-2": ("#a6bdf5", "#414b64"),
    "--heat-3": ("#7c9ef1", "#51628b"),
    "--heat-4": ("#517eec", "#6178b3"),
    # §3.11 UA 行为 (1)
    "--color-scheme": ("light", "dark"),
}

# --------------------------------------------------------------------------
# 43 组配对（权威表 §4.2 浅色 42 行 + §4.3 夜纸 42 行，按配对去重后 43 组）
#   (前景 token, 背景 token, 判定线, 备注)
#   判定线 0.0 = 面积档（不承载文字，无对比度要求）
#   备注以 "NA:" 开头 = **不适用**（配对本身不成立），不计入不达标项
# --------------------------------------------------------------------------
PAIRS = [
    ("--ink-strong", "--surface-base", 4.5, ""),
    ("--ink-strong", "--surface-card", 4.5, ""),
    ("--ink-strong", "--surface-raised", 4.5, ""),
    ("--ink-body", "--surface-base", 4.5, ""),
    ("--ink-body", "--surface-card", 4.5, ""),
    ("--ink-body", "--surface-raised", 4.5, ""),
    ("--ink-strong", "--surface-sunken", 4.5, ""),
    ("--ink-body", "--surface-sunken", 4.5, ""),
    ("--ink-muted", "--surface-sunken", 4.5, ""),
    ("--ink-faint", "--surface-sunken", 3.0, ""),
    ("--ink-body", "--surface-code", 4.5,
     "NA:权威表 §4.4-11 —— 代码面上的文字一律用 --ink-inverse，"
     "该配对本身不成立（浅色主题 1.37:1 是设计上的反白面，不是可读性缺陷）"),
    ("--ink-inverse", "--surface-code", 4.5, ""),
    ("--ink-muted", "--surface-base", 4.5, ""),
    ("--ink-muted", "--surface-card", 4.5, ""),
    ("--ink-faint", "--surface-base", 3.0, ""),
    ("--ink-faint", "--surface-card", 3.0, ""),
    ("--ink-faint", "--surface-raised", 3.0, ""),
    ("--ink-disabled", "--surface-base", 3.0, ""),
    ("--ink-disabled", "--surface-card", 3.0, ""),
    ("--ink-disabled", "--surface-raised", 3.0, ""),
    ("--role-blue", "--surface-base", 4.5, ""),
    ("--role-blue", "--surface-card", 4.5, ""),
    ("--role-blue", "--surface-raised", 4.5, ""),
    ("--role-blue", "--role-blue-wash", 4.5, ""),
    ("--ink-on-role", "--role-blue", 4.5, ""),
    ("--ink-on-role", "--role-blue-press", 4.5, ""),
    ("--ink-on-warm", "--role-yellow", 4.5, ""),
    ("--role-yellow-deep", "--surface-base", 3.0, ""),
    ("--role-yellow-deep", "--surface-card", 3.0, ""),
    ("--role-yellow", "--surface-base", 0.0, "面积档：黄色只承载面积与形状，不承载文字"),
    ("--role-red", "--surface-base", 3.0, ""),
    ("--role-red", "--surface-card", 3.0, ""),
    ("--role-red-ink", "--surface-base", 4.5, ""),
    ("--role-red-ink", "--surface-card", 4.5, ""),
    ("--role-red-ink", "--role-red-wash", 4.5, ""),
    ("--rule-control", "--surface-card", 3.0, ""),
    ("--rule-control", "--surface-base", 3.0, ""),
    ("--rule-control", "--surface-raised", 3.0, ""),
    ("--rule-structure", "--surface-card", 3.0, ""),
    ("--focus-outer", "--surface-card", 3.0, ""),
    ("--focus-outer", "--surface-base", 3.0, ""),
    ("--focus-inner", "--role-blue", 3.0, ""),
    ("--art-ink", "--art-paper", 3.0, ""),
]

# --------------------------------------------------------------------------
# WCAG 2.x 相对亮度与对比度（权威表 §4.1 的公式）
# --------------------------------------------------------------------------
def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lum(h):
    r, g, b = hex2rgb(h)
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# --------------------------------------------------------------------------
# 解析 CSS
# --------------------------------------------------------------------------
def block_values(css, selector):
    """取某个选择器块里的 (自定义属性名 -> 归一化取值)。"""
    i = css.find(selector)
    if i < 0:
        return {}
    j = css.find("{", i)
    depth, k = 0, j
    while k < len(css):
        if css[k] == "{":
            depth += 1
        elif css[k] == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    body = css[j + 1:k]
    out = {}
    for m in re.finditer(r"(--[A-Za-z0-9-]+)\s*:\s*([^;]+);", body):
        out[m.group(1)] = " ".join(m.group(2).split())
    return out


def default_css_path():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "workbench", "server", "static", "workbench.css")


def main(argv):
    path = argv[1] if len(argv) > 1 else default_css_path()
    try:
        css = open(path, encoding="utf-8").read()
    except OSError as exc:
        print("读不到 CSS：%s（%s）" % (path, exc), file=sys.stderr)
        return 2
    day = block_values(css, ":root {")
    night = block_values(css, 'html[data-theme="night"] {')
    if not day or not night:
        print("CSS 解析失败：找不到 :root 或 html[data-theme=\"night\"] 块", file=sys.stderr)
        return 2

    # ---------------- ① 值集核对（12.1）----------------
    print("=" * 96)
    print("① 夜纸值集核对（权威表 §3，%d 个值 token）—— 文件：%s" % (len(AUTH), path))
    print("=" * 96)
    missing, mismatch = [], []
    for name, (d, n) in sorted(AUTH.items()):
        for label, got, want in (("浅色", day.get(name), d), ("夜纸", night.get(name), n)):
            if got is None:
                missing.append("%s (%s)" % (name, label))
            elif got.replace(" ", "") != want.replace(" ", ""):
                mismatch.append("%s (%s): CSS=%r 权威=%r" % (name, label, got, want))
    print("缺失：%d 项 %s" % (len(missing), missing if missing else ""))
    print("不一致：%d 项" % len(mismatch))
    for m in mismatch:
        print("   ", m)
    print("（值集核对只作报告，不影响退出码 —— 退出码只看下面的对比度配对。）")

    # ---------------- ② 对比度复测表（12.3）----------------
    print()
    print("=" * 96)
    print("② 对比度复测表（WCAG 2.x；从 CSS 实际取值重算）")
    print("   判定线：正文/次要文字 ≥ 4.5:1 · 三级文字、控件边界与非文本 ≥ 3:1")
    print("=" * 96)
    header = ("| %-42s | %-7s | %-9s | %-9s | %-13s | %-13s |"
               % ("配对", "判定线", "浅色", "夜纸", "浅色结论", "夜纸结论"))
    print(header)
    print("|" + "-" * 42 + "|" + "-" * 7 + "|" + "-" * 9 + "|" + "-" * 9
          + "|" + "-" * 13 + "|" + "-" * 13 + "|")
    failures, not_applicable = [], []
    for fg, bg, line, note in PAIRS:
        f_d, b_d = day.get(fg), day.get(bg)
        f_n, b_n = night.get(fg), night.get(bg)
        if None in (f_d, b_d, f_n, b_n):
            print("| %-42s | %-7s | %-9s | %-9s | %-13s | %-13s |"
                  % ("%s / %s" % (fg.lstrip("-"), bg.lstrip("-")), line,
                     "取值缺失", "取值缺失", "ERROR", "ERROR"))
            failures.append("%s / %s：取值缺失" % (fg, bg))
            continue
        r_d, r_n = ratio(f_d, b_d), ratio(f_n, b_n)

        def verdict(r):
            if note.startswith("NA:"):
                return "不适用"
            if line == 0.0:
                return "PASS(面积档)"
            return "PASS" if r >= line else "FAIL"

        v_d, v_n = verdict(r_d), verdict(r_n)
        if note.startswith("NA:"):
            not_applicable.append("%s / %s" % (fg, bg))
        elif v_d == "FAIL" or v_n == "FAIL":
            failures.append("%s / %s：浅色 %.2f:1 / 夜纸 %.2f:1（判定线 %s）"
                            % (fg, bg, r_d, r_n, line))
        pair = "%s / %s" % (fg.lstrip("-"), bg.lstrip("-"))
        if note.startswith("NA:"):
            pair += "　※不适用"
        elif line == 0.0:
            pair += "　※面积档"
        print("| %-42s | %-7s | %-9s | %-9s | %-13s | %-13s |"
              % (pair, line if line else "—",
                 "%.2f:1" % r_d, "%.2f:1" % r_n, v_d, v_n))

    print()
    print("不适用配对（不计入不达标项）：%d 项 %s" % (len(not_applicable), not_applicable))
    for fg, bg, line, note in PAIRS:
        if note.startswith("NA:"):
            print("   %s / %s —— %s" % (fg, bg, note[3:]))
    print("低于判定线的配对：%d 项" % len(failures))
    for f in failures:
        print("   ", f)
    print()
    print("结论：%s" % ("全部适用配对达标。" if not failures
                        else "存在低于判定线的配对（见上）。"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
