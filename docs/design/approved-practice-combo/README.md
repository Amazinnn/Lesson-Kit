# 已批准 Combo 视觉基准

来源：本会话批准的 `meteor-motion/index.html?revision=7` 中 A「纸面方浪」横幅。用户在第三版明确表示 Combo 横幅无需补充；第四至七版只继续调整进度与交卷。原试样 README 记录：Figma 文件 `EanCMpoVqMfXqcr2HrJbqJ` 保持第三版，之后因 Starter MCP 额度未同步，以网页为动效评审依据。本轮尝试重新读取 Figma，再次返回额度限制，未伪称读取成功。

`combo.html`、`combo.css`、`combo-motion.js` 是批准网页组件与时间线的局部原文提取。正式 `practice-combo.js/css` 只适配作用域、唯一 SVG clip ID、业务节点与生命周期；不重画字形、画笔、色块或时间线。A 版暖白底、左黄块、底蓝带、红角块及原版 SVG 画笔为冻结基准，后续变更需用户明确批准。Georgia Italic 为原批准稿的矢量轮廓，不分发 Windows 字体文件。

## 视觉验收

`preview.html?source` 渲染批准稿，`preview.html` 渲染正式组件。相同 Chromium、尺寸、时间下比较 400ms（书写中）、1000ms（主体）、1750ms（退出）关键帧。`capture-check.js` 可由 Playwright 工具执行；先在仓库根目录以 3920 端口启动只读静态服务器。脚本逐帧比较完整截图字节，任何不一致立即失败。

2026-10-26 验证：桌面、窄屏和 375px CSS 视口的 9 对关键帧截图全部字节一致。保留一张批准稿截图 `approved-680-1000.png` 供人眼检查；脚本会重新生成并比较其余帧，不存重复图片。

`progress-0.png` 和 `progress-150.png` 展示中心与外圈先后亮起。浏览器还核对了间歇恢复浅象牙本色、26px 正方形、25 个像素、0px 边框、13px 圆角轨道以及填充层裁到头部右沿。
