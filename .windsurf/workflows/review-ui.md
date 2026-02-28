---
description: 审查前端 UI 代码质量，检查设计规范、无障碍、性能、交互等问题
---

# UI 审查 Workflow

对指定的前端组件/页面文件执行全面 UI 审查，基于 Vercel Web Interface Guidelines。

## 执行步骤

1. 读取用户指定的文件（或默认扫描 `web/src/components/` 和 `web/src/app/` 下的 `.tsx` 文件）

2. 按以下 11 个维度逐一检查，输出 `file:line — 问题描述` 格式的发现

---

## 审查维度与规则

### 1. 无障碍 (Accessibility)
- Icon-only 按钮必须有 `aria-label`
- 表单控件必须有 `<label>` 或 `aria-label`
- 交互元素需要键盘处理 (`onKeyDown`/`onKeyUp`)
- 操作用 `<button>`，导航用 `<a>`/`<Link>`，禁止 `<div onClick>`
- 图片必须有 `alt`（装饰性图片用 `alt=""`）
- 装饰性图标需要 `aria-hidden="true"`
- 异步状态更新 (toast/校验) 需要 `aria-live="polite"`
- 语义化 HTML 优先于 ARIA：`<button>`, `<a>`, `<label>`, `<table>`
- 标题层级 `<h1>`–`<h6>` 不跳级

### 2. 焦点状态 (Focus States)
- 交互元素必须有可见焦点：`focus-visible:ring-*` 或等效样式
- 禁止 `outline-none` / `outline: none` 除非有替代焦点样式
- 使用 `:focus-visible` 而非 `:focus`（避免点击时出现焦点环）

### 3. 表单 (Forms)
- 输入框需要 `autocomplete` 和有意义的 `name`
- 使用正确的 `type`（`email`, `tel`, `url`, `number`）和 `inputmode`
- 禁止阻止粘贴 (`onPaste` + `preventDefault`)
- Label 可点击（`htmlFor` 或包裹控件）
- 提交按钮在请求开始前保持可用；请求中显示 spinner
- 错误信息内联到字段旁；提交时聚焦第一个错误
- placeholder 以 `…` 结尾并展示示例格式

### 4. 动画 (Animation)
- 尊重 `prefers-reduced-motion`（提供简化变体或禁用）
- 只动画 `transform`/`opacity`（compositor-friendly）
- 禁止 `transition: all`，必须明确列出属性
- 动画可中断——响应用户输入中的动画

### 5. 排版 (Typography)
- 使用 `…` 而非 `...`
- Loading 状态以 `…` 结尾：`"加载中…"`, `"保存中…"`
- 数字列需要 `font-variant-numeric: tabular-nums`
- 标题使用 `text-wrap: balance` 或 `text-pretty` 防止孤字

### 6. 内容处理 (Content Handling)
- 文本容器处理长内容：`truncate`, `line-clamp-*`, 或 `break-words`
- Flex 子元素需要 `min-w-0` 以允许文本截断
- 处理空状态——空字符串/数组不渲染破碎 UI
- 考虑用户输入的极短、普通、超长三种情况

### 7. 图片 (Images)
- `<img>` 需要显式 `width` 和 `height`（防止 CLS）
- 首屏下方图片：`loading="lazy"`
- 首屏关键图片：`priority` 或 `fetchpriority="high"`

### 8. 性能 (Performance)
- 大列表 (>50 项)：虚拟化 (`virtua`, `content-visibility: auto`)
- 渲染中禁止 layout 读取 (`getBoundingClientRect`, `offsetHeight`)
- 受控输入必须保证每次按键轻量
- CDN/资源域名添加 `<link rel="preconnect">`
- 关键字体：`<link rel="preload" as="font">` + `font-display: swap`

### 9. 导航与状态 (Navigation & State)
- URL 反映状态——筛选、Tab、分页、展开面板放入 query params
- 链接使用 `<a>`/`<Link>`（支持 Cmd/Ctrl+click、中键点击）
- 所有有状态的 UI 都应可深度链接
- 危险操作需要确认弹窗或撤销窗口，不可立即执行

### 10. 触摸与交互 (Touch & Interaction)
- `touch-action: manipulation`（消除双击缩放延迟）
- Modal/Drawer 中使用 `overscroll-behavior: contain`
- `autoFocus` 谨慎使用——仅桌面端、单一主要输入

### 11. 暗色模式 (Dark Mode & Theming)
- 暗色主题设置 `color-scheme: dark` 在 `<html>` 上
- `<meta name="theme-color">` 匹配页面背景色
- 原生 `<select>` 需显式设置 `background-color` 和 `color`

---

## 反模式清单（必须标记）

发现以下任一模式时必须警告：

- `user-scalable=no` 或 `maximum-scale=1` 禁用缩放
- `onPaste` + `preventDefault` 阻止粘贴
- `transition: all`
- `outline-none` 无替代焦点样式
- 内联 `onClick` 导航未使用 `<a>`
- `<div>` / `<span>` 带 click handler（应为 `<button>`）
- 图片无尺寸
- 大数组 `.map()` 无虚拟化
- 表单输入无 label
- Icon 按钮无 `aria-label`
- 硬编码日期/数字格式（应用 `Intl.*`）
- `autoFocus` 无明确理由

---

## 输出格式

```
## UI 审查报告

### 🔴 严重 (必须修复)
- `src/components/foo.tsx:42` — Icon 按钮缺少 aria-label
- `src/app/page.tsx:18` — <div onClick> 应替换为 <button> 或 <Link>

### 🟡 建议 (推荐修复)
- `src/components/bar.tsx:15` — 文本容器缺少 truncate/line-clamp
- `src/app/layout.tsx:8` — 缺少 theme-color meta

### ✅ 良好实践
- Suspense 边界使用得当
- 表单有适当的 error handling
```
