const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright-core');

const ROOT = 'E:/coding-zhou/Python/python 日程表';
const APP = 'file:///' + ROOT + '/output/待办中心.html';
const XLSX_FILE = ROOT + '/测试待办数据.xlsx';
const SHOTS = ROOT + '/_src/shots';
const CHROME = 'C:/Users/Administrator/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe';

fs.mkdirSync(SHOTS, { recursive: true });

let pass = 0, fail = 0;
const failures = [];
function check(name, cond, extra) {
  if (cond) { pass++; console.log('  [PASS] ' + name); }
  else { fail++; failures.push(name + (extra ? ' :: ' + extra : '')); console.log('  [FAIL] ' + name + (extra ? ' :: ' + extra : '')); }
}
function section(t) { console.log('\n=== ' + t + ' ==='); }

// 用 DataTransfer 触发真正的 HTML5 拖放序列
async function nativeDrag(page, cardSel, colSel) {
  await page.evaluate(([cs, ts]) => {
    const card = document.querySelector(cs);
    const col = document.querySelector(ts);
    if (!card || !col) throw new Error('drag target missing: ' + cs + ' / ' + ts);
    const dt = new DataTransfer();
    card.dispatchEvent(new DragEvent('dragstart', { bubbles: true, cancelable: true, dataTransfer: dt }));
    col.dispatchEvent(new DragEvent('dragover', { bubbles: true, cancelable: true, dataTransfer: dt }));
    col.dispatchEvent(new DragEvent('drop', { bubbles: true, cancelable: true, dataTransfer: dt }));
    card.dispatchEvent(new DragEvent('dragend', { bubbles: true, cancelable: true, dataTransfer: dt }));
  }, [cardSel, colSel]);
}

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, acceptDownloads: true });
  const page = await ctx.newPage();

  const consoleErrors = [];
  const externalRequests = [];
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', e => consoleErrors.push('pageerror: ' + e.message));
  page.on('request', r => { if (!r.url().startsWith('file://') && !r.url().startsWith('data:') && !r.url().startsWith('blob:')) externalRequests.push(r.url()); });

  await page.goto(APP, { waitUntil: 'load' });
  await page.waitForTimeout(400);

  // ---------------------------------------------------------------- 基础
  section('基础结构');
  check('页面标题为「待办中心」', (await page.title()) === '待办中心', await page.title());
  check('侧边栏恰好 3 个导航项', await page.locator('.sidebar .nav-item').count() === 3);
  check('恰好 3 个页面容器', await page.locator('.page').count() === 3);
  check('无「团队」页面残留', await page.locator('#page-team').count() === 0);
  check('品牌名渲染为「待办中心」', (await page.locator('#brand-name').textContent()).trim() === '待办中心');
  check('侧边栏宽度为 240px', await page.evaluate(() => Math.round(document.querySelector('.sidebar').getBoundingClientRect().width)) === 240);
  check('日历为默认页', await page.locator('#page-calendar').evaluate(el => el.classList.contains('active')));

  const statsCount = await page.locator('#stats-grid .stat-card').count();
  check('日历页有 4 张统计卡片', statsCount === 4, '实际 ' + statsCount);
  const barCount = await page.locator('#progress-bars .progress-bar').count();
  check('进度条为 4 条', barCount === 4, '实际 ' + barCount);
  check('统计卡片数字使用等宽字体', await page.locator('.stat-card-value').first().evaluate(el => getComputedStyle(el).fontFamily.toLowerCase().includes('mono') || getComputedStyle(el).fontFamily.toLowerCase().includes('consolas')));
  const actCount0 = await page.locator('#activity-feed .activity-item').count();
  check('最近动态初始为空（种子不编造动态）', actCount0 === 0, '实际 ' + actCount0);
  check('动态空态提示可见', await page.locator('#activity-empty').isVisible());

  // ---------------------------------------------------------------- 看板
  section('看板与列');
  await page.click('.nav-item[data-page="kanban"]');
  await page.waitForTimeout(250);
  check('看板页已激活', await page.locator('#page-kanban').evaluate(el => el.classList.contains('active')));
  const cols = await page.locator('.kanban-column').count();
  check('看板为 4 列', cols === 4, '实际 ' + cols);
  const colTitles = await page.locator('.kanban-column-title').allTextContents();
  const titlesNorm = colTitles.map(t => t.replace(/\d+/g, '').trim());
  check('列顺序为 待办→进行中→审阅中→已完成',
    titlesNorm.join('|') === '待办|进行中|审阅中|已完成', titlesNorm.join('|'));

  const totalCards = await page.locator('.kanban-card').count();
  check('卡片总数为 13（示例数据）', totalCards === 13, '实际 ' + totalCards);
  check('卡片已移除负责人头像', await page.locator('.kanban-card-avatar').count() === 0);
  check('卡片显示优先级标签', await page.locator('.kanban-card-priority').count() === totalCards);
  check('卡片显示截止日期', await page.locator('.kanban-card-due').count() >= 13 - 0);
  check('存在逾期高亮（示例数据含过期项）', await page.locator('.kanban-card-due.overdue').count() > 0);

  // ---------------------------------------------------------------- 拖拽
  section('HTML5 拖拽流转');
  const beforeTodo = await page.locator('.kanban-column[data-status="todo"] .kanban-card').count();
  const beforeProg = await page.locator('.kanban-column[data-status="in-progress"] .kanban-card').count();
  const firstCardTitle = (await page.locator('.kanban-column[data-status="todo"] .kanban-card-title').first().textContent()).trim();

  await nativeDrag(page,
    '.kanban-column[data-status="todo"] .kanban-card',
    '.kanban-column[data-status="in-progress"] .kanban-cards');
  await page.waitForTimeout(400);

  const afterTodo = await page.locator('.kanban-column[data-status="todo"] .kanban-card').count();
  const afterProg = await page.locator('.kanban-column[data-status="in-progress"] .kanban-card').count();
  check('源列卡片 -1', afterTodo === beforeTodo - 1, beforeTodo + ' → ' + afterTodo);
  check('目标列卡片 +1', afterProg === beforeProg + 1, beforeProg + ' → ' + afterProg);

  const toastText = (await page.locator('#toast').textContent()).trim();
  check('拖拽后弹出 Toast', /移到/.test(toastText), toastText);
  check('Toast 处于显示状态', await page.locator('#toast').evaluate(el => el.classList.contains('show')));

  await page.waitForTimeout(400);
  const actTexts = await page.locator('#activity-feed .activity-item').allTextContents();
  check('动态日志记录了本次移动',
    actTexts.some(t => t.includes(firstCardTitle) && t.includes('进行中')),
    JSON.stringify(actTexts.slice(0, 2)));

  // 拖到已完成列 → 应记为「完成」
  await page.click('.nav-item[data-page="kanban"]');
  await nativeDrag(page,
    '.kanban-column[data-status="in-progress"] .kanban-card',
    '.kanban-column[data-status="done"] .kanban-cards');
  await page.waitForTimeout(350);
  const toast2 = (await page.locator('#toast').textContent()).trim();
  check('拖入已完成列提示「已完成」', toast2.includes('已完成'), toast2);

  // ---------------------------------------------------------------- 持久化
  section('localStorage 持久化');
  const stored = await page.evaluate(() => localStorage.getItem('todo-center-v1'));
  check('已写入 localStorage', !!stored && stored.length > 200);
  const parsed = JSON.parse(stored);
  check('存储结构含 tasks/activities/info/settings/ui',
    !!parsed.tasks && !!parsed.activities && !!parsed.info && !!parsed.settings && !!parsed.ui);
  check('拖拽状态已持久化（已完成列有卡片）',
    parsed.tasks.filter(t => t.status === 'done').length >= 1,
    '已完成 ' + parsed.tasks.filter(t => t.status === 'done').length);

  await page.reload({ waitUntil: 'load' });
  await page.waitForTimeout(400);
  check('刷新后回到上次所在页面', await page.locator('#page-kanban').evaluate(el => el.classList.contains('active')));
  const afterReloadCards = await page.locator('.kanban-card').count();
  check('刷新后数据仍在', afterReloadCards === totalCards, '实际 ' + afterReloadCards);

  // ---------------------------------------------------------------- 主题
  section('主题切换');
  const bgLight = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  await page.click('#theme-toggle');
  await page.waitForTimeout(300);
  const isDark = await page.evaluate(() => document.documentElement.classList.contains('dark'));
  const bgDark = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  check('切换后 html.dark 生效', isDark);
  check('背景色确实改变', bgLight !== bgDark, bgLight + ' → ' + bgDark);
  check('深色背景数值正确 (#09090b = rgb(9,9,11))', bgDark === 'rgb(9, 9, 11)', bgDark);
  check('data-theme 属性同步', await page.evaluate(() => document.documentElement.getAttribute('data-theme')) === 'dark');
  check('toggle 处于 active 态', await page.locator('#theme-toggle').evaluate(el => el.classList.contains('active')));
  const darkText = await page.evaluate(() => getComputedStyle(document.body).color);
  check('深色主题下文字为浅色', darkText === 'rgb(250, 250, 250)', darkText);
  await page.screenshot({ path: path.join(SHOTS, '02-kanban-dark.png') });

  // 深色下刷新，应记住主题
  await page.reload({ waitUntil: 'load' });
  await page.waitForTimeout(300);
  check('刷新后仍保持深色主题', await page.evaluate(() => document.documentElement.classList.contains('dark')));
  await page.click('#theme-toggle');
  await page.waitForTimeout(250);
  check('切回浅色主题', !(await page.evaluate(() => document.documentElement.classList.contains('dark'))));

  // ---------------------------------------------------------------- 快捷键
  section('键盘快捷键');
  await page.keyboard.press('Control+1');
  await page.waitForTimeout(250);
  check('Ctrl+1 → 日历', await page.locator('#page-calendar').evaluate(el => el.classList.contains('active')));
  await page.keyboard.press('Control+2');
  await page.waitForTimeout(250);
  check('Ctrl+2 → 待办看板', await page.locator('#page-kanban').evaluate(el => el.classList.contains('active')));
  await page.keyboard.press('Control+3');
  await page.waitForTimeout(250);
  check('Ctrl+3 → 设置', await page.locator('#page-settings').evaluate(el => el.classList.contains('active')));

  await page.keyboard.press('Control+n');
  await page.waitForTimeout(300);
  check('Ctrl+N → 打开新建弹窗', await page.locator('#task-modal').evaluate(el => el.classList.contains('show')));
  check('弹窗标题为「新建待办」', (await page.locator('#task-modal-title').textContent()).trim() === '新建待办');
  check('新建弹窗无「负责人」字段', await page.locator('#task-assignee').count() === 0);
  check('新建弹窗无「状态」字段（由目标列决定）', await page.locator('#task-status-group').isHidden());
  await page.keyboard.press('Escape');
  await page.waitForTimeout(320);
  check('Esc 关闭弹窗', !(await page.locator('#task-modal').evaluate(el => el.classList.contains('show'))));

  // ---------------------------------------------------------------- 新建 / 编辑 / 删除
  section('新建 · 编辑 · 删除待办');
  await page.click('.nav-item[data-page="kanban"]');
  await page.keyboard.press('Control+n');
  await page.waitForTimeout(300);
  await page.fill('#task-title', '端到端测试新建的待办');
  await page.click('#task-priority .priority-option[data-priority="high"]');
  await page.fill('#task-due', '2026-10-15');
  await page.click('#task-submit-btn');
  await page.waitForTimeout(400);
  const cnt1 = await page.locator('.kanban-card').count();
  check('新建后卡片 +1', cnt1 === totalCards + 1, totalCards + ' → ' + cnt1);
  check('新卡片出现在「待办」列', await page.locator('.kanban-column[data-status="todo"] .kanban-card', { hasText: '端到端测试新建的待办' }).count() === 1);
  check('新建成功有 Toast', (await page.locator('#toast').textContent()).includes('已创建'));

  // 点击卡片 → 编辑弹窗
  await page.locator('.kanban-card', { hasText: '端到端测试新建的待办' }).click();
  await page.waitForTimeout(350);
  check('点击卡片打开编辑弹窗', await page.locator('#task-modal').evaluate(el => el.classList.contains('show')));
  check('编辑弹窗标题正确', (await page.locator('#task-modal-title').textContent()).trim() === '编辑待办');
  check('编辑弹窗显示状态选择器', await page.locator('#task-status-group').isVisible());
  check('编辑弹窗显示删除按钮', await page.locator('#task-delete-btn').isVisible());
  check('标题已回填', (await page.inputValue('#task-title')) === '端到端测试新建的待办');
  check('日期已回填', (await page.inputValue('#task-due')) === '2026-10-15');

  await page.fill('#task-title', '端到端测试_已改名');
  await page.selectOption('#task-status', 'in-review');
  await page.click('#task-submit-btn');
  await page.waitForTimeout(400);
  check('改名生效', await page.locator('.kanban-card', { hasText: '端到端测试_已改名' }).count() === 1);
  check('状态改为审阅中后出现在审阅列',
    await page.locator('.kanban-column[data-status="in-review"] .kanban-card', { hasText: '端到端测试_已改名' }).count() === 1);

  // 删除 + 撤销
  await page.locator('.kanban-card', { hasText: '端到端测试_已改名' }).click();
  await page.waitForTimeout(320);
  await page.click('#task-delete-btn');
  await page.waitForTimeout(400);
  const cnt2 = await page.locator('.kanban-card').count();
  check('删除后卡片 -1', cnt2 === totalCards, '期望 ' + totalCards + ' 实际 ' + cnt2);
  check('删除 Toast 带「撤销」', (await page.locator('#toast .toast-action').textContent()).includes('撤销'));
  await page.click('#toast .toast-action');
  await page.waitForTimeout(400);
  const cnt3 = await page.locator('.kanban-card').count();
  check('点击撤销后卡片恢复', cnt3 === totalCards + 1, '期望 ' + (totalCards + 1) + ' 实际 ' + cnt3);

  // 清理：重新加载回干净状态供后续测试
  await page.evaluate(() => localStorage.removeItem('todo-center-v1'));
  await page.reload({ waitUntil: 'load' });
  await page.waitForTimeout(400);
  check('清除存储后回落到 13 条示例数据', await page.locator('.kanban-card').count() === 13);

  // ---------------------------------------------------------------- Excel 导入
  section('Excel 导入（使用真实文件）');
  await page.click('.nav-item[data-page="kanban"]');
  await page.waitForTimeout(200);
  await page.setInputFiles('#import-file', XLSX_FILE);
  await page.waitForTimeout(700);

  check('导入弹窗已打开', await page.locator('#import-modal').evaluate(el => el.classList.contains('show')));
  check('显示所选文件名', (await page.locator('#import-drop-title').textContent()).includes('测试待办数据.xlsx'));
  check('导入按钮已启用', !(await page.locator('#import-confirm').isDisabled()));

  const summary = (await page.locator('#import-summary').textContent()).replace(/\s+/g, ' ').trim();
  check('解析出 13 条待办', summary.includes('13'), summary);
  check('识别到工作表名 Sheet1', summary.includes('Sheet1'));
  check('给出日期范围 09-02 ~ 12-31', summary.includes('09-02') && summary.includes('12-31'), summary);

  const previewRows = await page.locator('#import-preview tbody tr').count();
  check('预览表格渲染 13 行', previewRows === 13, '实际 ' + previewRows);

  // 默认规则：9.2 → 09-02
  const firstDue = (await page.locator('#import-preview tbody tr').nth(1).locator('td.due').textContent()).trim();
  check('默认规则 9.2 → 09-02', firstDue === '09-02', firstDue);

  // 切换到补零规则：9.2 → 09-20
  await page.click('#import-rule .seg-item[data-rule="padded"]');
  await page.waitForTimeout(250);
  const paddedDue = (await page.locator('#import-preview tbody tr').nth(1).locator('td.due').textContent()).trim();
  check('切换补零规则后 9.2 → 09-20', paddedDue === '09-20', paddedDue);
  const padded3 = (await page.locator('#import-preview tbody tr').nth(7).locator('td.due').textContent()).trim();
  check('补零规则下 9.3 → 09-30', padded3 === '09-30', padded3);
  await page.click('#import-rule .seg-item[data-rule="literal"]');
  await page.waitForTimeout(200);
  const backDue = (await page.locator('#import-preview tbody tr').nth(1).locator('td.due').textContent()).trim();
  check('切回字面规则后恢复 09-02', backDue === '09-02', backDue);

  await page.screenshot({ path: path.join(SHOTS, '03-import-modal.png') });

  // 追加导入
  await page.click('#import-confirm');
  await page.waitForTimeout(700);
  const cntAfterImport = await page.locator('.kanban-card').count();
  check('追加导入后卡片 = 13 + 13 = 26', cntAfterImport === 26, '实际 ' + cntAfterImport);
  check('导入后跳到看板页', await page.locator('#page-kanban').evaluate(el => el.classList.contains('active')));
  const importToast = (await page.locator('#toast').textContent()).trim();
  check('导入 Toast 提示条数', importToast.includes('13'), importToast);

  const imported = await page.evaluate(() => {
    const d = JSON.parse(localStorage.getItem('todo-center-v1'));
    return d.tasks.filter(t => t.title === '提交上月考勤统计').length;
  });
  check('导入数据已持久化', imported === 2, '同标题数量 ' + imported);

  // 导入的日期应为当年（2026）
  const importedDue = await page.evaluate(() => {
    const d = JSON.parse(localStorage.getItem('todo-center-v1'));
    const t = d.tasks.filter(x => x.title === '国庆节假期开始');
    return t.length ? t[t.length - 1].due : null;
  });
  check('导入日期补全为 2026 年', importedDue === '2026-10-01', String(importedDue));

  // 替换导入
  await page.setInputFiles('#import-file', XLSX_FILE);
  await page.waitForTimeout(700);
  await page.click('#import-mode .seg-item[data-mode="replace"]');
  await page.waitForTimeout(200);
  await page.click('#import-confirm');
  await page.waitForTimeout(700);
  const cntReplace = await page.locator('.kanban-card').count();
  check('替换导入后卡片 = 13（不叠加）', cntReplace === 13, '实际 ' + cntReplace);

  // 空文件
  await page.setInputFiles('#import-file', ROOT + '/7777777.xlsx');
  await page.waitForTimeout(700);
  const emptyToast = (await page.locator('#toast').textContent()).trim();
  check('空表格给出友好提示而非崩溃', emptyToast.includes('没有解析到') || emptyToast.includes('无'), emptyToast);
  check('空表格不打开导入弹窗', !(await page.locator('#import-modal').evaluate(el => el.classList.contains('show'))));

  // ---------------------------------------------------------------- 导出
  section('导出');
  await page.click('.nav-item[data-page="settings"]');
  await page.waitForTimeout(300);
  const [dl] = await Promise.all([
    page.waitForEvent('download', { timeout: 15000 }),
    page.click('button:has-text("导出 Excel")')
  ]);
  const dlPath = path.join(SHOTS, 'export-test.xlsx');
  await dl.saveAs(dlPath);
  const dlSize = fs.statSync(dlPath).size;
  check('导出 Excel 成功且非空', dlSize > 2000, dlSize + ' bytes');
  check('导出文件名含时间戳', /待办中心-\d{8}-\d{4}\.xlsx/.test(dl.suggestedFilename()), dl.suggestedFilename());

  const [dl2] = await Promise.all([
    page.waitForEvent('download', { timeout: 15000 }),
    page.click('button:has-text("导出 JSON")')
  ]);
  const jsonPath = path.join(SHOTS, 'export-test.json');
  await dl2.saveAs(jsonPath);
  const exported = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
  check('JSON 备份含 13 条待办', exported.tasks.length === 13, '实际 ' + exported.tasks.length);

  // 往返闭环：把刚导出的 Excel 再喂给导入器
  await page.setInputFiles('#import-file', dlPath);
  await page.waitForTimeout(800);
  check('导出的 Excel 可被自己重新导入', await page.locator('#import-modal').evaluate(el => el.classList.contains('show')));
  const rtRows = await page.locator('#import-preview tbody tr').count();
  check('往返后仍解析出 13 条', rtRows === 13, '实际 ' + rtRows);
  const rtFirst = (await page.locator('#import-preview tbody tr').nth(2).locator('td.due').textContent()).trim();
  check('往返后日期未漂移（9.15 → 09-15）', rtFirst === '09-15', rtFirst);
  await page.click('#import-mode .seg-item[data-mode="replace"]');
  await page.waitForTimeout(200);
  await page.click('#import-confirm');
  await page.waitForTimeout(700);
  check('往返导入后仍是 13 条', await page.locator('.kanban-card').count() === 13, '实际 ' + await page.locator('.kanban-card').count());

  // 数据管理统计
  const dataStats = (await page.locator('#data-stats').textContent()).replace(/\s+/g, ' ');
  check('数据管理卡片显示统计', dataStats.includes('待办条数') && dataStats.includes('KB'), dataStats.trim());

  // ---------------------------------------------------------------- 设置项
  section('设置项实际生效');
  await page.click('.nav-item[data-page="settings"]');   // 导入流程会把视图切到看板，先切回设置
  await page.waitForTimeout(300);
  const doneColBefore = await page.locator('.kanban-column[data-status="done"]').count();
  await page.click('.toggle[data-setting="showDoneColumn"]');
  await page.waitForTimeout(300);
  check('关闭后开关态变更', !(await page.locator('.toggle[data-setting="showDoneColumn"]').evaluate(el => el.classList.contains('active'))));
  await page.click('.nav-item[data-page="kanban"]');
  await page.waitForTimeout(300);
  const doneColAfter = await page.locator('.kanban-column[data-status="done"]').count();
  check('关闭「已完成列」后看板只剩 3 列', doneColBefore === 1 && doneColAfter === 0, doneColBefore + ' → ' + doneColAfter);
  check('看板副标题提示已隐藏', (await page.locator('#kanban-subtitle').textContent()).includes('已隐藏'));
  await page.screenshot({ path: path.join(SHOTS, '05-kanban-3cols.png') });

  await page.click('.nav-item[data-page="settings"]');
  await page.click('.toggle[data-setting="showDoneColumn"]');
  await page.waitForTimeout(200);
  await page.click('.nav-item[data-page="kanban"]');
  await page.waitForTimeout(250);

  // 紧凑模式
  await page.click('.nav-item[data-page="settings"]');
  const padBefore = await page.evaluate(() => getComputedStyle(document.querySelector('.kanban-card') || document.body).padding);
  await page.click('.toggle[data-setting="compact"]');
  await page.waitForTimeout(250);
  check('紧凑模式给 body 加 class', await page.evaluate(() => document.body.classList.contains('compact')));
  await page.click('.nav-item[data-page="kanban"]');
  await page.waitForTimeout(250);
  const padAfter = await page.evaluate(() => getComputedStyle(document.querySelector('.kanban-card')).padding);
  check('紧凑模式确实收窄卡片内边距', padBefore !== padAfter, padBefore + ' → ' + padAfter);
  check('紧凑模式已持久化', await page.evaluate(() => JSON.parse(localStorage.getItem('todo-center-v1')).settings.compact === true));

  // 清单信息
  await page.click('.nav-item[data-page="settings"]');
  await page.fill('#settings-name', '我的日程');
  await page.fill('#settings-desc', '每天推进一点点');
  await page.click('button:has-text("保存修改")');
  await page.waitForTimeout(350);
  check('清单名称同步到侧边栏', (await page.locator('#brand-name').textContent()).trim() === '我的日程');
  check('浏览器标题同步', (await page.title()) === '我的日程');
  check('品牌图标取首字', (await page.locator('#brand-icon').textContent()).trim() === '我');
  await page.click('.nav-item[data-page="calendar"]');
  await page.waitForTimeout(300);
  check('清单描述同步到日历副标题', (await page.locator('#cal-subtitle').textContent()).includes('每天推进一点点'));
  await page.screenshot({ path: path.join(SHOTS, '01-dashboard-light.png') });

  // 危险区 + 确认弹窗
  section('危险区域与确认流');
  await page.click('.nav-item[data-page="settings"]');
  await page.waitForTimeout(250);
  await page.click('button:has-text("清空全部待办")');
  await page.waitForTimeout(300);
  check('打开确认弹窗', await page.locator('#confirm-modal').evaluate(el => el.classList.contains('show')));
  check('确认弹窗说明条数', (await page.locator('#confirm-body').textContent()).includes('13'));
  await page.click('#confirm-ok');
  await page.waitForTimeout(500);
  check('清空后 0 张卡片', await page.locator('.kanban-card').count() === 0);
  check('所有列显示为 0 或仅剩表头', await page.locator('.kanban-card').count() === 0);
  await page.click('#toast .toast-action');
  await page.waitForTimeout(500);
  check('撤销后恢复 13 张卡片', await page.locator('.kanban-card').count() === 13, '实际 ' + await page.locator('.kanban-card').count());

  // 空状态渲染
  await page.click('button:has-text("清空全部待办")');
  await page.waitForTimeout(250);
  await page.click('#confirm-ok');
  await page.waitForTimeout(400);
  await page.click('.nav-item[data-page="calendar"]');
  await page.waitForTimeout(400);
  const zeroStats = await page.locator('.stat-card-value').allTextContents();
  check('空数据下统计全为 0（无除零/NaN）', zeroStats.join('') === '0000', zeroStats.join('|'));
  check('空数据下无 NaN', !(await page.locator('#stats-grid').textContent()).includes('NaN'));
  await page.screenshot({ path: path.join(SHOTS, '06-dashboard-empty.png') });

  await page.click('.nav-item[data-page="settings"]');
  await page.waitForTimeout(250);
  await page.click('button:has-text("恢复为初始示例数据")');
  await page.waitForTimeout(250);
  await page.click('#confirm-ok');
  await page.waitForTimeout(500);
  check('恢复示例数据后回到 13 条', await page.locator('.kanban-card').count() === 13);

  // ---------------------------------------------------------------- 清空动态
  section('动态日志');
  await page.click('.nav-item[data-page="kanban"]');
  await page.waitForTimeout(300);
  // 种子不含任何动态，先做一个真实操作生成一条
  await page.locator('.card-quick-check').first().click();
  await page.waitForTimeout(350);
  await page.click('.nav-item[data-page="calendar"]');
  await page.waitForTimeout(300);
  const actBefore = await page.locator('#activity-feed .activity-item').count();
  check('操作后动态日志有内容', actBefore > 0, '实际 ' + actBefore);
  await page.click('#clear-activity-btn');
  await page.waitForTimeout(350);
  check('清空动态后显示空状态', await page.locator('#activity-empty').isVisible());
  await page.click('#toast .toast-action');
  await page.waitForTimeout(400);
  check('撤销后动态恢复', await page.locator('#activity-feed .activity-item').count() === actBefore);

  // ---------------------------------------------------------------- 响应式
  section('响应式布局');
  for (const w of [1440, 1024, 768, 390]) {
    await page.setViewportSize({ width: w, height: 900 });
    await page.waitForTimeout(350);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    check(w + 'px 无横向溢出', overflow <= 1, '溢出 ' + overflow + 'px');
  }

  await page.setViewportSize({ width: 1024, height: 900 });
  await page.click('.nav-item[data-page="calendar"]');
  await page.waitForTimeout(350);
  const statCols1024 = await page.locator('#stats-grid').evaluate(el => getComputedStyle(el).gridTemplateColumns.split(' ').length);
  check('1024px 统计卡片为双列', statCols1024 === 2, '实际 ' + statCols1024 + ' 列');
  await page.screenshot({ path: path.join(SHOTS, '04-dashboard-1024.png') });

  await page.setViewportSize({ width: 768, height: 900 });
  await page.click('.mobile-tab[data-page="kanban"]');
  await page.waitForTimeout(400);
  const boardDir = await page.locator('#kanban-board').evaluate(el => getComputedStyle(el).flexDirection);
  check('768px 看板竖排 (column)', boardDir === 'column', boardDir);
  check('768px 侧边栏隐藏', await page.locator('.sidebar').isHidden());
  check('768px 底部导航出现', await page.locator('.mobile-nav').isVisible());
  check('768px 底部导航有 3 个 tab', await page.locator('.mobile-tab').count() === 3);
  await page.screenshot({ path: path.join(SHOTS, '07-mobile-768.png'), fullPage: true });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(400);
  const statColsMobile = await page.locator('#stats-grid').evaluate(el => getComputedStyle(el).gridTemplateColumns.split(' ').length);
  check('390px 统计卡片单列', statColsMobile === 1, '实际 ' + statColsMobile);
  await page.click('.mobile-tab[data-page="calendar"]');
  await page.waitForTimeout(350);
  check('底部导航可切页', await page.locator('#page-calendar').evaluate(el => el.classList.contains('active')));
  await page.screenshot({ path: path.join(SHOTS, '08-mobile-390.png'), fullPage: true });
  await page.setViewportSize({ width: 1440, height: 900 });

  // ---------------------------------------------------------------- 离线 / 错误
  section('离线零依赖与运行时错误');
  check('全程无外部网络请求', externalRequests.length === 0, JSON.stringify(externalRequests.slice(0, 5)));
  check('无 JS 运行时错误', consoleErrors.length === 0, JSON.stringify(consoleErrors.slice(0, 5)));

  const offlineOk = await page.evaluate(() => {
    try { return typeof XLSX !== 'undefined' && typeof XLSX.read === 'function' && typeof XLSX.write === 'function'; }
    catch (e) { return false; }
  });
  check('XLSX 库已内联且 read/write 可用', offlineOk);

  await ctx.setOffline(true);
  const offlineReload = await page.reload({ waitUntil: 'load' }).then(() => true).catch(() => false);
  await page.waitForTimeout(400);
  check('断网后仍能正常加载', offlineReload && await page.locator('.kanban-card').count() === 13, '卡片数 ' + await page.locator('.kanban-card').count());
  await ctx.setOffline(false);

  // ---------------------------------------------------------------- 对比度
  section('可访问性：设计令牌对比度（WCAG 2.1）');
  const contrast = await page.evaluate(() => {
    function hex2rgb(h) {
      const m = /^#([0-9a-f]{6})$/i.exec(String(h).trim());
      if (!m) return null;
      const n = parseInt(m[1], 16);
      return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
    }
    function lum(rgb) {
      const c = rgb.map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
      return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
    }
    function ratio(a, b) {
      const l1 = lum(a), l2 = lum(b), hi = Math.max(l1, l2), lo = Math.min(l1, l2);
      return (hi + 0.05) / (lo + 0.05);
    }
    function read(theme) {
      const wasDark = document.documentElement.classList.contains('dark');
      document.documentElement.classList.toggle('dark', theme === 'dark');
      const s = getComputedStyle(document.documentElement);
      const bg = hex2rgb(s.getPropertyValue('--bg-primary'));
      const card = hex2rgb(s.getPropertyValue('--card-bg'));
      const out = {
        primary: ratio(hex2rgb(s.getPropertyValue('--text-primary')), bg),
        secondary: ratio(hex2rgb(s.getPropertyValue('--text-secondary')), bg),
        tertiary: ratio(hex2rgb(s.getPropertyValue('--text-tertiary')), bg),
        tertiaryOnCard: ratio(hex2rgb(s.getPropertyValue('--text-tertiary')), card)
      };
      document.documentElement.classList.toggle('dark', wasDark);
      return out;
    }
    return { light: read('light'), dark: read('dark') };
  });

  console.log('  浅色: 主文 ' + contrast.light.primary.toFixed(2) + ' / 次文 ' + contrast.light.secondary.toFixed(2) +
    ' / 元信息 ' + contrast.light.tertiary.toFixed(2));
  console.log('  深色: 主文 ' + contrast.dark.primary.toFixed(2) + ' / 次文 ' + contrast.dark.secondary.toFixed(2) +
    ' / 元信息 ' + contrast.dark.tertiary.toFixed(2));

  check('深色主文字 ≥ 12:1（AAA）', contrast.dark.primary >= 12, contrast.dark.primary.toFixed(2));
  check('深色次文字 ≥ 4.5:1（AA）', contrast.dark.secondary >= 4.5, contrast.dark.secondary.toFixed(2));
  check('深色元信息 ≥ 4.5:1（AA，修复前仅 2.40）', contrast.dark.tertiary >= 4.5, contrast.dark.tertiary.toFixed(2));
  check('浅色主文字 ≥ 12:1（AAA）', contrast.light.primary >= 12, contrast.light.primary.toFixed(2));
  check('浅色次文字 ≥ 4.5:1（AA）', contrast.light.secondary >= 4.5, contrast.light.secondary.toFixed(2));
  check('浅色元信息 ≥ 3.1:1（Linear 式低对比元信息下限）', contrast.light.tertiary >= 3.1, contrast.light.tertiary.toFixed(2));
  check('卡片上元信息在深色下 ≥ 4.5:1', contrast.dark.tertiaryOnCard >= 4.5, contrast.dark.tertiaryOnCard.toFixed(2));

  // ---------------------------------------------------------------- 收尾截图
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.click('.nav-item[data-page="kanban"]');
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(SHOTS, '00-kanban-light.png') });
  await page.click('.nav-item[data-page="calendar"]');
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(SHOTS, '00-dashboard-top.png') });
  await page.click('.nav-item[data-page="settings"]');
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(SHOTS, '00-settings-light.png'), fullPage: true });

  await browser.close();

  console.log('\n' + '='.repeat(60));
  console.log('通过 ' + pass + ' / ' + (pass + fail));
  if (fail) {
    console.log('\n失败项:');
    failures.forEach(f => console.log('  - ' + f));
  }
  console.log('='.repeat(60));
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('测试脚本异常:', e); process.exit(2); });
