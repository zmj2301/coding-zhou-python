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

// 预期的种子（与 测试待办数据.xlsx 完全一致，全部待办/默认优先级/无动态）
const EXPECT_TITLES = ['提交上月考勤统计', '完成季度工作汇报 PPT', '和设计师对接悬浮球界面稿', '整理本周开发笔记',
  '测试桌面悬浮球缩小与恢复', '验证待办倒计时每秒实时刷新', '提交悬浮球功能测试反馈', '完成 9 月工作总结',
  '国庆节假期开始', '假期结束，回到岗位', '双十一项目促销值班', '参加年终复盘会议', '和团队一起跨年'];

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, acceptDownloads: true });
  const page = await ctx.newPage();

  const consoleErrors = [];
  const externalRequests = [];
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', e => consoleErrors.push('pageerror: ' + e.message));
  page.on('request', r => { if (!/^(file|data|blob):/.test(r.url())) externalRequests.push(r.url()); });

  await page.goto(APP, { waitUntil: 'load' });
  await page.waitForTimeout(400);

  // ---------------------------------------------------------------- 结构
  section('日历结构');
  check('页面标题为「待办中心」', (await page.title()) === '待办中心', await page.title());
  check('侧边栏 3 个导航项', await page.locator('.sidebar .nav-item').count() === 3);
  check('首项导航为「日历」', (await page.locator('.sidebar .nav-item').first().textContent()).includes('日历'));
  check('默认页为日历', await page.locator('#page-calendar').evaluate(el => el.classList.contains('active')));
  check('无「仪表盘」页面残留', await page.locator('#page-dashboard').count() === 0);
  check('日历容器已渲染', await page.locator('#calendar').count() === 1);
  check('统计卡片仍为 4 张', await page.locator('#stats-grid .stat-card').count() === 4);
  check('有周/月切换器', await page.locator('#cal-view-switch .seg-item').count() === 2);

  // ---------------------------------------------------------------- 种子真实性（不瞎编）
  section('种子真实性（不瞎编）');
  const seed = await page.evaluate(() => {
    const d = JSON.parse(localStorage.getItem('todo-center-v1'));
    return d;
  });
  check('种子恰为 13 条', seed.tasks.length === 13, '实际 ' + seed.tasks.length);
  const statuses = [...new Set(seed.tasks.map(t => t.status))];
  check('全部初始为「待办」（不编造状态）', statuses.length === 1 && statuses[0] === 'todo', JSON.stringify(statuses));
  const prios = [...new Set(seed.tasks.map(t => t.priority))];
  check('全部默认优先级（不编造优先级）', prios.length === 1 && prios[0] === 'medium', JSON.stringify(prios));
  check('无「负责人」字段', seed.tasks.every(t => !('assignee' in t)), '');
  check('动态日志为空（不编造历史）', seed.activities.length === 0, '实际 ' + seed.activities.length);
  const titles = seed.tasks.map(t => t.title).sort();
  check('标题与 Excel 完全一致', JSON.stringify(titles) === JSON.stringify([...EXPECT_TITLES].sort()), titles.slice(0, 3).join('/'));
  const dues = seed.tasks.filter(t => t.due).map(t => t.due).sort();
  check('所有待办都有 2026 年日期', dues.every(d => d.startsWith('2026-')), dues.slice(0, 3).join(','));
  check('空动态显示空状态提示', await page.locator('#activity-empty').isVisible());

  // ---------------------------------------------------------------- 周视图
  section('周视图渲染');
  const dayCols = await page.locator('.cal-week .cal-day').count();
  check('周视图为 7 列', dayCols === 7, '实际 ' + dayCols);
  const wdTexts = (await page.locator('.cal-day-wd').allTextContents()).map(s => s.trim());
  check('列头为 周一~周日', wdTexts.join('') === '周一周二周三周四周五周六周日', wdTexts.join(','));
  check('恰好 1 个「今天」高亮列', await page.locator('.cal-day.today').count() === 1);
  check('今天列对应真实日期', await page.evaluate(() => {
    const el = document.querySelector('.cal-day.today');
    return el && el.dataset.date === (function(){ const d=new Date(); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); })();
  }));
  check('显示「第 N 周」', /第\s*\d+\s*周/.test(await page.locator('#cal-subtitle').textContent()), await page.locator('#cal-subtitle').textContent());
  check('月份标题正确', /\d{4} 年 \d{1,2} 月/.test(await page.locator('#cal-title').textContent()), await page.locator('#cal-title').textContent());

  const chipTotal = await page.locator('.cal-week .cal-chip').count();
  check('本周内待办以卡片呈现（本周 5 条）', chipTotal === 5, '实际 ' + chipTotal);
  check('09-27 列含「提交悬浮球功能测试反馈」',
    await page.locator('.cal-day[data-date="2026-09-27"] .cal-chip-title', { hasText: '提交悬浮球功能测试反馈' }).count() === 1);
  check('09-26 列含 2 条待办', await page.locator('.cal-day[data-date="2026-09-26"] .cal-chip').count() === 2);
  check('种子全部有日期，「未安排」区为空', await page.locator('.cal-unscheduled .cal-chip').count() === 0, '实际 ' + await page.locator('.cal-unscheduled .cal-chip').count());
  check('「未安排」区显示空态提示', (await page.locator('.cal-unscheduled .cal-empty-inline').textContent()).includes('全部待办都已安排日期'));

  await page.screenshot({ path: path.join(SHOTS, '10-calendar-week.png') });

  // ---------------------------------------------------------------- 拖拽改期
  section('拖拽改期');
  await nativeDrag(page,
    '.cal-day[data-date="2026-09-27"] .cal-chip',
    '.cal-day[data-date="2026-09-26"]');
  await page.waitForTimeout(400);
  const resched = await page.evaluate(() => {
    const d = JSON.parse(localStorage.getItem('todo-center-v1'));
    const t = d.tasks.find(x => x.title === '提交悬浮球功能测试反馈');
    return { due: t.due, acts: d.activities.length };
  });
  check('拖拽后截止日期改为 09-26', resched.due === '2026-09-26', resched.due);
  check('09-26 列现含 3 条', await page.locator('.cal-day[data-date="2026-09-26"] .cal-chip').count() === 3);
  check('改期写入动态日志', resched.acts === 1, '实际 ' + resched.acts);
  check('改期 Toast 提示', (await page.locator('#toast').textContent()).includes('改期'));

  // 拖出日历 → 取消日期
  await nativeDrag(page,
    '.cal-day[data-date="2026-09-26"] .cal-chip',
    '.cal-unscheduled');
  await page.waitForTimeout(400);
  const unsched = await page.evaluate(() => {
    const d = JSON.parse(localStorage.getItem('todo-center-v1'));
    return d.tasks.filter(t => !t.due).length;
  });
  check('拖入「未安排」后该待办日期被清空', unsched === 1, '实际 ' + unsched);
  check('移出 Toast 提示', (await page.locator('#toast').textContent()).includes('取消日期'));

  // 还原
  await page.evaluate(() => localStorage.removeItem('todo-center-v1'));
  await page.reload({ waitUntil: 'load' });
  await page.waitForTimeout(400);

  // ---------------------------------------------------------------- 点击编辑 / 新建
  section('点击编辑与按日新建');
  await page.locator('.cal-day[data-date="2026-09-24"] .cal-chip').first().click();
  await page.waitForTimeout(350);
  check('点击卡片打开编辑弹窗', await page.locator('#task-modal').evaluate(el => el.classList.contains('show')));
  check('日期已回填 09-24', (await page.inputValue('#task-due')) === '2026-09-24', await page.inputValue('#task-due'));
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);

  await page.locator('.cal-day[data-date="2026-09-25"] .cal-add').click();
  await page.waitForTimeout(350);
  check('按日「＋」打开新建弹窗', (await page.locator('#task-modal-title').textContent()).trim() === '新建待办');
  check('新建预填该日 09-25', (await page.inputValue('#task-due')) === '2026-09-25', await page.inputValue('#task-due'));
  await page.fill('#task-title', '在 9/25 加的待办');
  await page.click('#task-submit-btn');
  await page.waitForTimeout(400);
  check('新建后 09-25 列含该待办',
    await page.locator('.cal-day[data-date="2026-09-25"] .cal-chip-title', { hasText: '在 9/25 加的待办' }).count() === 1);
  await page.evaluate(() => localStorage.removeItem('todo-center-v1'));
  await page.reload({ waitUntil: 'load' });
  await page.waitForTimeout(400);

  // ---------------------------------------------------------------- 周导航
  section('周导航');
  const title0 = await page.locator('#cal-title').textContent();
  await page.click('button[aria-label="下一个周期"]');
  await page.waitForTimeout(350);
  const chipsNext = await page.locator('.cal-week .cal-chip').count();
  check('下一周显示 10-01 的待办', chipsNext >= 1, '实际 ' + chipsNext);
  check('下周有「国庆节假期开始」',
    await page.locator('.cal-week .cal-chip-title', { hasText: '国庆节假期开始' }).count() === 1);
  await page.click('button:has-text("今天")');
  await page.waitForTimeout(350);
  check('「今天」按钮回到当前周', (await page.locator('#cal-title').textContent()) === title0);
  await page.click('button[aria-label="上一个周期"]');
  await page.waitForTimeout(300);
  check('上一周可正常渲染', await page.locator('.cal-week .cal-day').count() === 7);
  await page.click('button:has-text("今天")');
  await page.waitForTimeout(300);

  // ---------------------------------------------------------------- 月视图
  section('月视图');
  await page.click('#cal-view-switch .seg-item[data-view="month"]');
  await page.waitForTimeout(400);
  const cells = await page.locator('.cal-month-grid .cal-cell').count();
  check('月视图为 42 格（6×7）', cells === 42, '实际 ' + cells);
  check('月视图有星期表头', (await page.locator('.cal-weekhead .cal-wd').allTextContents()).join('') === '周一周二周三周四周五周六周日');
  check('月视图恰 1 个今天高亮', await page.locator('.cal-cell.today').count() === 1);
  check('月视图含相邻月灰色格', await page.locator('.cal-cell.other-month').count() > 0);
  check('9/26 格内显示 2 条', await page.locator('.cal-cell[data-date="2026-09-26"] .cal-mchip').count() === 2);
  check('月标题为 2026 年 9 月', (await page.locator('#cal-title').textContent()).includes('9 月'), await page.locator('#cal-title').textContent());
  await page.screenshot({ path: path.join(SHOTS, '11-calendar-month.png') });

  await page.click('button[aria-label="下一个周期"]');
  await page.waitForTimeout(350);
  check('月导航到下月（10 月）', (await page.locator('#cal-title').textContent()).includes('10 月'), await page.locator('#cal-title').textContent());
  check('10/01 格含「国庆节假期开始」',
    await page.locator('.cal-cell[data-date="2026-10-01"] .cal-chip-title', { hasText: '国庆节假期开始' }).count() === 1);
  await page.click('button:has-text("今天")');
  await page.waitForTimeout(300);

  // 月视图拖拽改期
  await nativeDrag(page,
    '.cal-cell[data-date="2026-09-27"] .cal-mchip',
    '.cal-cell[data-date="2026-09-23"]');
  await page.waitForTimeout(400);
  const mresched = await page.evaluate(() => {
    const d = JSON.parse(localStorage.getItem('todo-center-v1'));
    return d.tasks.find(x => x.title === '提交悬浮球功能测试反馈').due;
  });
  check('月视图拖拽改期生效（→ 09-23）', mresched === '2026-09-23', mresched);
  await page.evaluate(() => localStorage.removeItem('todo-center-v1'));
  await page.reload({ waitUntil: 'load' });
  await page.waitForTimeout(400);
  await page.click('#cal-view-switch .seg-item[data-view="week"]');
  await page.waitForTimeout(300);

  // ---------------------------------------------------------------- 看板与设置未回归
  section('看板 / 设置未回归');
  await page.click('.nav-item[data-page="kanban"]');
  await page.waitForTimeout(350);
  check('看板仍 4 列', await page.locator('.kanban-column').count() === 4);
  check('看板 13 张卡片', await page.locator('.kanban-card').count() === 13);
  await page.click('.nav-item[data-page="settings"]');
  await page.waitForTimeout(350);
  check('设置页快捷键写「切换到日历」', (await page.locator('.shortcut-list').textContent()).includes('切换到日历'));

  // ---------------------------------------------------------------- 导入回归
  section('导入回归');
  await page.click('.nav-item[data-page="kanban"]');
  await page.waitForTimeout(250);
  await page.setInputFiles('#import-file', XLSX_FILE);
  await page.waitForTimeout(700);
  check('导入弹窗打开', await page.locator('#import-modal').evaluate(el => el.classList.contains('show')));
  const summary = (await page.locator('#import-summary').textContent()).replace(/\s+/g, ' ');
  check('导入解析 13 条', summary.includes('13'), summary);
  await page.click('#import-confirm');
  await page.waitForTimeout(700);
  check('追加导入后 26 张卡片', await page.locator('.kanban-card').count() === 26, '实际 ' + await page.locator('.kanban-card').count());
  await page.evaluate(() => localStorage.removeItem('todo-center-v1'));
  await page.reload({ waitUntil: 'load' });
  await page.waitForTimeout(400);

  // ---------------------------------------------------------------- 主题 / 快捷键 / 持久化
  section('主题 · 快捷键 · 持久化');
  await page.click('#theme-toggle');
  await page.waitForTimeout(300);
  check('深色主题生效', await page.evaluate(() => document.documentElement.classList.contains('dark')));
  check('深色下日历今天高亮仍在', await page.locator('.cal-day.today').count() === 1);
  await page.screenshot({ path: path.join(SHOTS, '12-calendar-dark.png') });
  await page.click('#theme-toggle');
  await page.waitForTimeout(250);

  await page.keyboard.press('Control+1');
  await page.waitForTimeout(250);
  check('Ctrl+1 → 日历', await page.locator('#page-calendar').evaluate(el => el.classList.contains('active')));
  await page.keyboard.press('Control+2');
  await page.waitForTimeout(250);
  check('Ctrl+2 → 看板', await page.locator('#page-kanban').evaluate(el => el.classList.contains('active')));

  await page.evaluate(() => {
    const d = JSON.parse(localStorage.getItem('todo-center-v1'));
    d.ui.page = 'calendar';
    localStorage.setItem('todo-center-v1', JSON.stringify(d));
  });
  await page.reload({ waitUntil: 'load' });
  await page.waitForTimeout(400);
  check('刷新后回到日历页', await page.locator('#page-calendar').evaluate(el => el.classList.contains('active')));
  check('刷新后 13 张看板卡片仍在', await page.locator('.kanban-card').count() === 13);

  // ---------------------------------------------------------------- 保存回 Excel
  section('调整后保存回 Excel');
  check('日历页有「保存为 Excel」按钮', await page.locator('#save-excel-btn').count() === 1);
  check('未改动时无「未导出」圆点', !(await page.locator('#save-excel-wrap').evaluate(el => el.classList.contains('has-unsaved'))));
  check('未改动时提示条隐藏', !(await page.locator('#unsaved-pill').evaluate(el => el.classList.contains('show'))));

  // 先导出一份「未改动」的，用来和源文件逐行比对
  const [dl0] = await Promise.all([
    page.waitForEvent('download', { timeout: 15000 }),
    page.click('#save-excel-btn')
  ]);
  await dl0.saveAs(path.join(SHOTS, 'saved-clean.xlsx'));
  check('未调整即可导出，文件名同源文件', dl0.suggestedFilename() === '测试待办数据.xlsx', dl0.suggestedFilename());
  await page.waitForTimeout(300);

  await nativeDrag(page,
    '.cal-day[data-date="2026-09-27"] .cal-chip',
    '.cal-day[data-date="2026-09-26"]');
  await page.waitForTimeout(400);
  check('改期已即时落盘到 localStorage', await page.evaluate(() => {
    const d = JSON.parse(localStorage.getItem('todo-center-v1'));
    return d.tasks.find(x => x.title === '提交悬浮球功能测试反馈').due === '2026-09-26';
  }));
  check('调整后出现未导出圆点', await page.locator('#save-excel-wrap').evaluate(el => el.classList.contains('has-unsaved')));
  check('调整后显示「有改动未导出」', await page.locator('#unsaved-pill').evaluate(el => el.classList.contains('show')));

  const [dl] = await Promise.all([
    page.waitForEvent('download', { timeout: 15000 }),
    page.click('#save-excel-btn')
  ]);
  const savedPath = path.join(SHOTS, 'saved.xlsx');
  await dl.saveAs(savedPath);
  fs.writeFileSync(path.join(SHOTS, 'saved-name.txt'), dl.suggestedFilename(), 'utf8');
  check('导出文件名 = 源文件名（可直接覆盖）', dl.suggestedFilename() === '测试待办数据.xlsx', dl.suggestedFilename());
  check('导出文件非空', fs.statSync(savedPath).size > 2000, fs.statSync(savedPath).size + ' bytes');
  check('导出后圆点消失', !(await page.locator('#save-excel-wrap').evaluate(el => el.classList.contains('has-unsaved'))));
  check('导出 Toast 提示可覆盖原文件', (await page.locator('#toast').textContent()).includes('覆盖'), await page.locator('#toast').textContent());
  await page.reload({ waitUntil: 'load' });
  await page.waitForTimeout(400);
  check('刷新后「已导出」状态被记住', !(await page.locator('#save-excel-wrap').evaluate(el => el.classList.contains('has-unsaved'))));

  // ---------------------------------------------------------------- 悬浮全文提示
  section('长标题悬浮显示完整内容');
  await page.evaluate(() => localStorage.removeItem('todo-center-v1'));
  await page.reload({ waitUntil: 'load' });
  await page.waitForTimeout(500);
  const chipSel = '.cal-day[data-date="2026-09-27"] .cal-chip';
  check('chip 挂了完整文本 data-full',
    (await page.locator(chipSel).first().getAttribute('data-full')) === '提交悬浮球功能测试反馈',
    await page.locator(chipSel).first().getAttribute('data-full'));
  check('chip 标题确实被截断',
    await page.locator(chipSel + ' .cal-chip-title').first().evaluate(el => el.scrollWidth > el.clientWidth + 1));

  await page.locator(chipSel).first().hover();
  await page.waitForTimeout(500);
  check('悬停后提示条出现', await page.locator('#full-tip.show').count() === 1);
  const tipText = (await page.locator('#full-tip').textContent()).replace(/\s+/g, ' ').trim();
  check('提示显示完整标题', tipText.includes('提交悬浮球功能测试反馈'), tipText);
  check('提示副行含状态 / 优先级 / 日期', /待办/.test(tipText) && /中/.test(tipText) && /09-27/.test(tipText), tipText);
  check('提示框未溢出视口', await page.locator('#full-tip').evaluate(el => {
    const r = el.getBoundingClientRect();
    return r.left >= 0 && r.top >= 0 && r.right <= window.innerWidth && r.bottom <= window.innerHeight;
  }));
  await page.screenshot({ path: path.join(SHOTS, '14-tooltip.png') });

  await page.mouse.move(900, 24);
  await page.waitForTimeout(300);
  check('鼠标移开后提示消失', await page.locator('#full-tip.show').count() === 0);

  await page.click('.nav-item[data-page="kanban"]');
  await page.waitForTimeout(350);
  check('看板卡片标题同样挂了 data-full',
    (await page.locator('.kanban-card-title').first().getAttribute('data-full') || '').length > 0);
  await page.click('.nav-item[data-page="calendar"]');
  await page.waitForTimeout(300);

  // ---------------------------------------------------------------- 响应式
  section('响应式');
  for (const w of [1440, 1024, 768, 390]) {
    await page.setViewportSize({ width: w, height: 900 });
    await page.waitForTimeout(350);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    check(w + 'px 无横向溢出', overflow <= 1, '溢出 ' + overflow + 'px');
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.click('.mobile-tab[data-page="calendar"]');
  await page.waitForTimeout(400);
  check('移动端日历可横向滚动或自适应', await page.locator('.cal-week, .cal-month-grid').count() >= 1);
  await page.screenshot({ path: path.join(SHOTS, '13-calendar-mobile.png'), fullPage: true });
  await page.setViewportSize({ width: 1440, height: 900 });

  // ---------------------------------------------------------------- 离线 / 错误
  section('离线零依赖与运行时错误');
  check('全程无外部网络请求', externalRequests.length === 0, JSON.stringify(externalRequests.slice(0, 5)));
  check('无 JS 运行时错误', consoleErrors.length === 0, JSON.stringify(consoleErrors.slice(0, 5)));
  await ctx.setOffline(true);
  await page.reload({ waitUntil: 'load' }).catch(() => {});
  await page.waitForTimeout(400);
  check('断网后日历仍正常', await page.locator('.cal-week .cal-day').count() === 7);
  await ctx.setOffline(false);

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
