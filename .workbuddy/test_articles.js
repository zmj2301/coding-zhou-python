// 技术文章页面冒烟测试：加载首页 → 切到文章视图 → 校验列表/阅读器
const { chromium } = require('playwright-core');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true,
    args: ['--no-sandbox'],
  });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));

  await page.goto('file:///E:/coding-zhou/Python/code-explorer/index.html', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(3000);
  // 绕过 file:// 下的登录门（线上由 /api/auth-check 判定，不影响真实站点）
  await page.evaluate(() => { const ap = document.querySelector('#authPage'); if (ap) ap.classList.remove('active'); });

  // 1) 侧边栏入口存在
  const navExists = await page.evaluate(() => !!document.getElementById('navArticles'));
  console.log('navArticles 存在:', navExists);

  // 2) 切换到文章视图
  await page.evaluate(() => switchSidebarView('articles'));
  await page.waitForTimeout(500);
  const r1 = await page.evaluate(() => ({
    pageShown: document.getElementById('articlesPage').style.display,
    cards: document.querySelectorAll('.art-card').length,
    firstTitle: (document.querySelector('.art-card-title') || {}).textContent || ''
  }));
  console.log('列表视图:', JSON.stringify(r1));

  // 3) 打开第一篇（v2.6.9）
  await page.evaluate(() => artShowArticle(0));
  await page.waitForTimeout(300);
  const r2 = await page.evaluate(() => ({
    readerShown: document.getElementById('articlesReaderView').style.display,
    title: document.getElementById('artReaderTitle').textContent.slice(0, 30),
    hasH2: document.querySelectorAll('#artReaderContent .art-h2').length,
    hasTable: document.querySelectorAll('#artReaderContent .art-table').length,
    hasPre: document.querySelectorAll('#artReaderContent .art-pre').length,
    contentLen: document.getElementById('artReaderContent').innerHTML.length
  }));
  console.log('阅读器:', JSON.stringify(r2));

  // 4) 打开第二篇（事故复盘）并检查标题渲染
  await page.evaluate(() => artShowList());
  await page.evaluate(() => artShowArticle(1));
  const r3 = await page.evaluate(() => ({
    title: document.getElementById('artReaderTitle').textContent.slice(0, 20),
    blocks: document.getElementById('artReaderContent').children.length
  }));
  console.log('文章2:', JSON.stringify(r3));

  // 5) 文章3（第一篇排查文章，最长）
  await page.evaluate(() => artShowArticle(2));
  const r4 = await page.evaluate(() => ({
    blocks: document.getElementById('artReaderContent').children.length,
    quotes: document.querySelectorAll('#artReaderContent .art-quote').length,
    checks: document.querySelectorAll('#artReaderContent .art-check.done').length
  }));
  console.log('文章1(最长):', JSON.stringify(r4));

  // 截图留档
  await page.evaluate(() => artShowList());
  await page.waitForTimeout(300);
  await page.screenshot({ path: 'E:/coding-zhou/Python/.workbuddy/articles_list.png' });
  await page.evaluate(() => artShowArticle(1));
  await page.waitForTimeout(300);
  await page.screenshot({ path: 'E:/coding-zhou/Python/.workbuddy/articles_reader.png' });

  console.log('JS 错误数:', errors.length);
  errors.slice(0, 5).forEach(e => console.log('  ', e.slice(0, 120)));
  await browser.close();
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
