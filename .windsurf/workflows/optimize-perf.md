---
description: 优化 React/Next.js 前端性能，检查瀑布流请求、包体积、服务端渲染、客户端数据获取、重渲染、渲染性能等问题
---

# 前端性能优化 Workflow

对指定的前端代码执行性能审查，基于 Vercel React Best Practices（按优先级排序）。

## 执行步骤

1. 读取用户指定的文件（或默认扫描 `web/src/` 下所有 `.tsx`/`.ts` 文件）
2. 按 8 个优先级维度逐一检查
3. 输出发现，按严重程度分级

---

## 审查维度（按优先级排序）

### P1. 消除瀑布流请求 (CRITICAL)

**影响：2-10× 性能提升**

- **async-parallel**: 独立的 async 操作必须用 `Promise.all()` 并行
  ```ts
  // ❌ 串行 3 次往返
  const user = await fetchUser()
  const posts = await fetchPosts()
  // ✅ 并行 1 次往返
  const [user, posts] = await Promise.all([fetchUser(), fetchPosts()])
  ```

- **async-defer-await**: 把 `await` 移到真正需要结果的分支
  ```ts
  // ❌ 总是等待
  const data = await fetchData()
  if (condition) return data
  // ✅ 只在需要时等待
  const dataPromise = fetchData()
  if (condition) return await dataPromise
  ```

- **async-suspense**: 使用 Suspense 边界流式渲染，不阻塞整个页面
  ```tsx
  // ❌ 整个页面被数据阻塞
  async function Page() {
    const data = await fetchData()
    return <Layout><Data data={data} /></Layout>
  }
  // ✅ Layout 立即渲染，数据流式加载
  function Page() {
    return <Layout><Suspense fallback={<Skeleton/>}><Data/></Suspense></Layout>
  }
  ```

- **async-api-routes**: API Route 中尽早启动 promise，尽晚 await

### P2. 包体积优化 (CRITICAL)

- **bundle-barrel-imports**: 直接导入具体文件，避免 barrel 文件（index.ts 重导出）
  ```ts
  // ❌ import { Button } from '@/components'  (拉入整个 barrel)
  // ✅ import { Button } from '@/components/ui/button'
  ```

- **bundle-dynamic-imports**: 重型组件用 `next/dynamic` 懒加载
  ```tsx
  const HeavyChart = dynamic(() => import('./Chart'), { ssr: false })
  ```

- **bundle-defer-third-party**: 分析/日志等三方库在 hydration 后加载
- **bundle-conditional**: 功能未激活时不加载对应模块
- **bundle-preload**: 悬停/聚焦时预加载提升感知速度

### P3. 服务端性能 (HIGH)

- **server-cache-react**: 使用 `React.cache()` 实现请求级去重
- **server-cache-lru**: 跨请求缓存用 LRU Map
- **server-dedup-props**: 避免 RSC props 重复序列化（同一数据传多个组件）
- **server-serialization**: 最小化传给 Client Component 的数据
  ```tsx
  // ❌ 传整个对象
  <ClientComp data={fullObject} />
  // ✅ 只传需要的字段
  <ClientComp name={fullObject.name} count={fullObject.items.length} />
  ```
- **server-parallel-fetching**: 重组组件结构使数据获取并行
- **server-after-nonblocking**: 用 `after()` 处理非阻塞操作（日志、分析）

### P4. 客户端数据获取 (MEDIUM-HIGH)

- **client-swr-dedup**: 使用 SWR 自动请求去重
- **client-event-listeners**: 全局事件监听器去重
- **client-passive-event-listeners**: 滚动事件用 `{ passive: true }`
- **client-localstorage-schema**: localStorage 数据加版本号，最小化

### P5. 重渲染优化 (MEDIUM)

- **rerender-defer-reads**: 不订阅只在回调中用的 state
- **rerender-memo**: 提取昂贵计算到 memo 化组件
- **rerender-derived-state**: 订阅派生布尔值，不订阅原始大对象
- **rerender-derived-state-no-effect**: 在渲染时派生 state，不用 useEffect
  ```tsx
  // ❌ useEffect 里 setState
  useEffect(() => { setFiltered(items.filter(fn)) }, [items])
  // ✅ 渲染时直接计算
  const filtered = useMemo(() => items.filter(fn), [items])
  ```
- **rerender-functional-setstate**: 使用函数式 setState 获得稳定回调
- **rerender-lazy-state-init**: 昂贵的初始值传函数给 useState
  ```tsx
  // ❌ 每次渲染都计算
  const [state] = useState(expensiveComputation())
  // ✅ 只计算一次
  const [state] = useState(() => expensiveComputation())
  ```
- **rerender-transitions**: 非紧急更新用 `startTransition`

### P6. 渲染性能 (MEDIUM)

- **rendering-content-visibility**: 长列表用 `content-visibility: auto`
- **rendering-hoist-jsx**: 静态 JSX 提取到组件外部
- **rendering-conditional-render**: 条件渲染用三元运算符，不用 `&&`
  ```tsx
  // ❌ count 为 0 时渲染 "0"
  {count && <Badge>{count}</Badge>}
  // ✅ 安全
  {count > 0 ? <Badge>{count}</Badge> : null}
  ```
- **rendering-usetransition-loading**: 用 `useTransition` 代替手动 loading state
- **rendering-hydration-no-flicker**: 客户端数据用内联 script 防闪烁

### P7. JavaScript 性能 (LOW-MEDIUM)

- **js-batch-dom-css**: CSS 变更通过 class 批量应用
- **js-index-maps**: 重复查找用 Map 建索引
- **js-combine-iterations**: 多次 filter/map 合并为单次循环
- **js-set-map-lookups**: O(1) 查找用 Set/Map 代替 Array.includes
- **js-early-exit**: 函数尽早 return
- **js-hoist-regexp**: RegExp 提到循环外部

### P8. 高级模式 (LOW)

- **advanced-init-once**: 应用级初始化只执行一次
- **advanced-event-handler-refs**: 事件处理器存 ref 避免依赖变化
- **advanced-use-latest**: useLatest 获取稳定回调引用

---

## 输出格式

```
## 性能审查报告

### 🔴 CRITICAL (必须修复)
- `src/app/page.tsx:25` — [async-parallel] fetchUser 和 fetchPosts 串行请求，应用 Promise.all
- `src/components/foo.tsx:10` — [bundle-barrel] 从 barrel 文件导入，应直接导入具体模块

### 🟡 HIGH/MEDIUM (建议修复)
- `src/components/bar.tsx:42` — [rerender-derived-state] useEffect 中 setState 派生数据，改为 useMemo
- `src/app/layout.tsx:8` — [server-serialization] 传了完整对象给 Client Component

### ✅ 良好实践
- Suspense 边界使用得当
- 动态导入用于重型组件
```
