# Python 子项目集成问题排查：一次"改了却没生效"的完整复盘

> 项目：Code Explorer（codingzhou.top）
> 时间：2026-09-30 ~ 2026-10-01
> 版本：v2.6.7 / v2.6.8
> 关键词：Cloudflare Worker、build.py、双文件陷阱、层级浏览、分支切换回退

---

## 一、背景

Code Explorer 是一个教学项目代码浏览与在线运行平台，架构是典型的混合部署：

- **Cloudflare Worker**（`code-explorer/worker.ts`）做主入口：SSR + API 代理；
- **阿里云 ECS**（`ecs-server.py :8765`）负责 AI 推理和文件服务；
- **GitHub 仓库** 提供静态资源；
- **KV** 缓存 GitHub 请求。

这次要解决的问题有两个：

1. **README 加载问题**——项目卡片的 README 抽屉内容加载异常；
2. **Python 子项目集成**——希望点进 Python 相关项目时能更直接地进入编辑界面，而不是每次都绕"卡片 → README 抽屉 → 预览"三步。

## 二、第一轮改造：Python 独立页（v2.6.7）

最初的方案是把 `code-explorer/python/index.html` 从"只能跑示例代码的空白编辑器"改造成 **Python 项目广场 + 在线编辑器**。

改造中发现了两个真实问题：

### 问题 1：Python 页面空白

原代码调用的是 `/api/files/tree`——**这个端点需要登录**。未登录状态下接口静默失败，页面自然一片空白。

**修复**：改用公开的 `/api/projects/tree?path=Python&depth=2`，无需登录即可拉取项目树。

### 问题 2：项目文件树 404

Worker 代理 ECS 时，带 `Python/` 前缀的路径（如 `Python/codinghou`）会失败。

**修复**：去掉 `Python/` 前缀——顶层项目直接用目录名（如 `python 3D射击`），codinghou 子项目用 `codinghou/AI扑克牌`。这样 ECS 和 GitHub fallback 两条链路都能正确处理。

### 线上验证

| API | 结果 |
|---|---|
| `/api/projects/tree?path=Python` | ✅ 149 节点（55 目录 + 94 文件） |
| `/api/projects/tree?path=codinghou` | ✅ 返回全部子项目 |
| `/api/projects/tree?path=python 3D射击` | ✅ 返回文件列表 |
| `/api/projects/readme?path=python 3D射击` | ✅ 返回完整 README |

Worker 部署成功（Version ID: `fe00ac0e`），changelog 更新到 v2.6.7。**看似完事。**

## 三、第二轮：需求走偏了

用户反馈一针见血：

> 我说的是跟右侧"项目广场"类似，只是这里面的内容是 Python 的。点击"项目广场"里的 Python 卡片后，希望进入下一层，且内容变为 Python 文件夹。另外，你给的这个样式跟现在的完全不一样。

翻译一下真实需求：

- ❌ 不是要一个独立的 `/python/` 页面；
- ✅ 是在**主站首页**，点 Python 卡片 → **同一页面**下钻一层，展示 Python 子目录卡片；
- ✅ 样式必须**完全复用**现有的紫色渐变卡片，不能另起炉灶。

### 层级浏览实现（两轮迭代）

第二轮先实现了 `navigateFolder` 版本（+277 / -11），第三轮在浏览器实测后重写为更简洁的 `enterPythonFolder / exitPythonFolder / handleProjectCardClick` 版本（+82 / -9，零 CSS 改动），完全复用现有 `buildProjects()`、`classifyProject`、`getProjectDesc` 等函数，卡片外观与项目广场一模一样。

交互流程：

```
项目广场首页（16 个紫色卡片）
  ↓ 点 Python 卡片
面包屑：🏠首页 / Python  [返回]
展示 Python 子目录（55+ 个同款卡片，自动分类 + 图标）
  ↓ 点 python 3D射击 卡片
面包屑：🏠首页 / Python / python 3D射击  [返回]
README 抽屉 → 点"开始" → 编辑器打开（文件树 265 节点 + Monaco + 终端）
  ↑ 面包屑任意层级可直接跳回
```

只对 Python 开启下钻，白名单一行搞定：

```javascript
const FOLDER_NEEDS_SUBDIR = ['Python', 'codinghou', 'workbody'];
```

## 四、第三轮：代码明明对，用户却说"点不动"

用户再次反馈：

> 我的意思是点了这个按钮能进去，你，我感觉好像没有那个呀

于是直接上浏览器实测：点击 Python 卡片后——**弹出的是"Python 项目说明"弹窗**，层级逻辑根本没生效。在 console 里检查新增函数：**全部 MISSING**。

改动根本没进部署包。

### 根因：build.py 的"双 index.html"陷阱

追查构建链路，真相大白：

| 文件 | 大小 | 修改时间 | 说明 |
|---|---|---|---|
| `index.html`（**根目录**） | 403KB | 9/27 | build.py 实际复制的，**旧版** ❌ |
| `code-explorer/index.html` | 304KB | 当天 | 一直被修改的，**新版** ✅ |

`build.py` 位于项目根目录，它的 `CODE_EXPLORER_DIR = Path(__file__).resolve().parent` 解析出的就是根目录——于是构建时把**根目录那份 9/27 的旧 index.html** 复制进 `public/`。

结论：**连续 3 次 build + deploy，部署上线的全是旧版本。** 没有 `folderStack`、没有面包屑、没有层级函数，点卡片当然没反应。

### 修复

```bash
# 用新版覆盖根目录旧文件
cp code-explorer/index.html index.html
# 重新构建 + 部署
python build.py && npx wrangler deploy
```

### 部署后实测验证

| 测试 | 结果 |
|---|---|
| 首页恢复原版 | 16 张卡片、返回按钮隐藏 ✅ |
| 点 Python 卡片 | 55 张子目录卡片，标题变"Python"，返回按钮出现 ✅ |
| 自动分类 | python 3D射击 → 游戏 🕹️，python AI实战 → AI 🤖 ✅ |
| 点子项目卡片 | README 抽屉正常弹出 ✅ |
| 点"开始" | 编辑器打开，文件树 265 节点加载成功 ✅ |
| 面包屑返回 | 逐层回退，首页状态完全恢复 ✅ |

## 五、意外插曲：分支切换把未提交改动全部抹掉（10-01）

10-01 下午按计划清理遗留待办时，发现 16:38 工作区发生了一次**批量回退**：v2.6.7 的所有未提交改动（首页层级浏览、python 页重写、changelog 条目）全部消失，变回旧版本。git 历史揭示了根因：

```
55b6840 [Checkout-checkpoint] from win7-compat to main (16:38:44)
```

一次 IDE 的分支切换检查点（从 `win7-compat` 切回 `main`）把未提交的工作区改动全部覆盖。

**恢复方式出乎意料地简单：线上站点还保有全部最新版本。** 从 `https://codingzhou.top/`、`/python/`、`/changelog.json` 下载部署产物写回源码（Worker 对首页的注入只有特定路由下的 `__INITIAL_PROJECTS__`，静态资源本身干净），逐一 grep 特征函数验证后恢复完毕。

这也再次印证：**部署出去的版本就是一份天然备份**——前提是它确实是最新版。

## 六、复盘：四条教训

1. **构建源必须单一事实源。** 同一个页面存在两份拷贝（根目录 + `code-explorer/`），而构建脚本引用的恰好是旧的那份——改 100 次代码也不会上线。v2.6.8 已根治：`code-explorer/index.html` 为唯一规范源，build.py 构建时校验两份一致性，**不一致直接中止构建**。

2. **"部署成功"≠"改动生效"。** wrangler 输出 `✨ Success!` 只代表包上去了，不代表包里是新代码。部署后必须在真实浏览器里验证新增函数/DOM 是否存在（本次就是靠 console 检查 MISSING 才定位到根因）。

3. **需求确认要看到实物。** 第一轮做了独立 `/python/` 页面，方向就错了——用户要的是"项目广场里的层级浏览"。一张交互流程图或原型截图，比三段文字描述更能对齐预期。

4. **改完尽快提交，尤其是多分支并行开发时。** 一次 `win7-compat → main` 的分支切换就把 main 上所有未提交改动抹掉了。未提交的工作区状态是最脆弱的。

## 七、遗留事项处理结果（v2.6.8，2026-10-01 全部完成）

- [x] 移除 `code-explorer/worker.ts` 中 `/api/projects/tree` 路由里的调试 `console.log`（保留正常错误日志）；
- [x] build.py 单一事实源改造：规范源 `code-explorer/index.html`，不一致中止构建，AGENTS.md 新增 3.6 节记录规则；
- [x] 从线上站点恢复被分支切换回退的 v2.6.7 未提交改动；
- [x] changelog 更新至 v2.6.8，Worker 已重新部署（Version ID: `f9d03fdd`），KV 缓存已清空，线上验证通过；
- [x] GitHub push：已重试（本次提交 13 万行变更，网络较慢，后台推送中）；
- ℹ️ `FOLDER_NEEDS_SUBDIR` 目前仅 Python 开启，如需给 `codinghou` / `workbody` 开启，改一行白名单即可。

---

*本文基于 2026-09-30 ~ 10-01 的排查会话整理，覆盖 v2.6.7 的三轮迭代与 v2.6.8 的收尾治理。*
