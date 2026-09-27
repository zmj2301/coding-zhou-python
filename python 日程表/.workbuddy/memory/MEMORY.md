# 项目长期记忆

## 项目性质
`python 日程表` 目录原本是 Python 桌面日程/待办相关实验（`ai.py`、`show_yourwindows.py`、`日程表.spec`、`build_exe.py`、`dist/*.exe` 等）。2026-09-27 新增了一个**纯前端的单文件待办工具**，与原有 Python 代码互不依赖。

## 待办中心（Web 工具）
- 成品：`output/待办中心.html`（单文件、零外部网络请求）
- 源码：`_src/todo-app.template.html` + `_src/build.py`
- **改代码流程**：改模板 → 跑 `python _src/build.py` → 产物覆盖 `output/待办中心.html`。不要直接编辑成品（内联了 273KB 的 SheetJS，不可读）。
- 验收：`NODE_PATH=<node workspace>/node_modules <managed node> _src/e2e.js`（需 `playwright-core`，浏览器用 `~/AppData/Local/ms-playwright` 里已有的 Chromium）；日历功能验收跑 `_src/calendar-e2e.js`
- 技术栈约定：**零框架、无外部请求**、CSS 变量驱动深浅色、localStorage 持久化、内联依赖走构建注入
- 主视图是**日历**（周/月切换，默认页），看板为第二页；种子数据由 build.py 从 `测试待办数据.xlsx` 真实提取注入（`/*__SEED__*/`），**禁止编造**
- 「未安排日期」区 = 无截止日期的待办；日历拖拽支持改期 / 拖入未安排清空日期
- 「保存为 Excel」导出与源文件同构的两列 xlsx（数字型月.日、还原浮点脏值），默认文件名 = 最近导入的源文件名，可直接覆盖原文件；改动未导出时按钮带琥珀色圆点
- 长标题截断时 hover 显示反色 tooltip（`data-full` 委托实现，仅真截断才弹）；校验导出用 `_src/verify_export.py`

## 本地 Excel 待办数据格式（用户固有习惯）
两列 `time` + `things`；`time` 是**数字型「月.日」**（如 `9.15`、`9.2`、`12.31`），无年份。
- 坑：`9.2` 与 `9.20` 在 Excel 中同值，无法区分 9月2日/9月20日；`9.199999999999999` 是浮点误差，需 `Math.round(v*100)/100` 修正。
- 导入时用当年年份补全；把 `9.2` 当 **9月2日** 是字面默认，另有「补零」规则可切换。
