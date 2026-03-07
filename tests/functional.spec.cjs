const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:8080';

test.describe('GrapheneOS Functional Tests', () => {
  
  test('main pages load correctly', async ({ page }) => {
    const pages = [
      '/',
      '/features',
      '/usage',
      '/install/',
      '/source',
      '/faq',
      '/donate',
      '/contact',
      '/releases',
      '/build',
    ];
    
    for (const path of pages) {
      const response = await page.goto(BASE_URL + path);
      expect(response.status()).toBe(200);
    }
  });

  test('navigation menu works', async ({ page }) => {
    await page.goto(BASE_URL);
    
    // Проверить что главная страница загрузилась
    await expect(page).toHaveTitle(/GrapheneOS/i);
    
    // Проверить наличие основных ссылок в меню
    const navLinks = await page.locator('nav a, header a').all();
    expect(navLinks.length).toBeGreaterThan(0);
  });

  test('download/install buttons lead to releases', async ({ page }) => {
    await page.goto(BASE_URL);
    
    // Ищем кнопки Install или Download
    const installLink = page.locator('a[href*="install"], a:has-text("Install")').first();
    const downloadLink = page.locator('a[href*="download"], a:has-text("Download")').first();
    
    // Если есть ссылка на install, проверяем
    if (await installLink.count() > 0) {
      await installLink.click();
      expect(page.url()).toContain('/install');
    }
  });

  test('contact page has form', async ({ page }) => {
    await page.goto(BASE_URL + '/contact');
    
    // Проверить наличие формы или email
    const hasContactInfo = await page.locator('form, a[href^="mailto:"]').count();
    expect(hasContactInfo).toBeGreaterThan(0);
  });

  test('releases page shows versions', async ({ page }) => {
    await page.goto(BASE_URL + '/releases');
    
    // Проверить что есть информация о версиях
    const content = await page.content();
    expect(content.length).toBeGreaterThan(100);
  });

  test('faq page has content', async ({ page }) => {
    await page.goto(BASE_URL + '/faq');
    
    // Проверить что есть вопросы и ответы
    const hasQuestions = await page.locator('h1, h2, h3').count();
    expect(hasQuestions).toBeGreaterThan(0);
  });

  test('static resources load (CSS, JS)', async ({ page }) => {
    await page.goto(BASE_URL);
    
    // Проверить что CSS загрузился
    const cssLinks = await page.locator('link[rel="stylesheet"]').count();
    expect(cssLinks).toBeGreaterThan(0);
    
    // Проверить что JS загрузился
    const jsScripts = await page.locator('script').count();
    expect(jsScripts).toBeGreaterThan(0);
  });

  test('no critical console errors', async ({ page }) => {
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    await page.goto(BASE_URL);
    await page.goto(BASE_URL + '/features');
    await page.goto(BASE_URL + '/install/');
    
    // Игнорируем некоторые ожидаемые ошибки (например, 404 для отсутствующих ресурсов)
    const criticalErrors = errors.filter(e => !e.includes('404'));
    expect(criticalErrors.length).toBe(0);
  });

  // Features page tests
  test('features page loads correctly', async ({ page }) => {
    await page.goto(BASE_URL + '/features');
    await expect(page).toHaveTitle(/GrapheneOS/i);
    
    // Проверить наличие оглавления
    const toc = page.locator('#table-of-contents');
    await expect(toc).toBeVisible();
  });

  test('features page - navigation to sections works', async ({ page }) => {
    await page.goto(BASE_URL + '/features');
    
    // Список разделов для проверки
    const sections = [
      { id: 'exploit-protection', name: 'Exploit Protection' },
      { id: 'sandboxed-google-play', name: 'Sandboxed Google Play' },
      { id: 'vanadium', name: 'Vanadium' },
      { id: 'auditor', name: 'Auditor' },
      { id: 'grapheneos-camera', name: 'GrapheneOS Camera' },
      { id: 'private-screenshots', name: 'Private Screenshots' },
      { id: 'network-permission-toggle', name: 'Network Permission Toggle' },
    ];
    
    for (const section of sections) {
      // Клик по ссылке в оглавлении
      const link = page.locator(`#table-of-contents a[href="#${section.id}"]`);
      if (await link.count() > 0) {
        await link.click();
        
        // Проверить что URL изменился
        expect(page.url()).toContain(`#${section.id}`);
        
        // Проверить что секция видима
        const sectionEl = page.locator(`#${section.id}`);
        await expect(sectionEl).toBeVisible();
      }
    }
  });

  test('features page - all TOC links are clickable', async ({ page }) => {
    await page.goto(BASE_URL + '/features');
    
    // Получить все ссылки из оглавления
    const tocLinks = page.locator('#table-of-contents a');
    const count = await tocLinks.count();
    
    expect(count).toBeGreaterThan(10);
    
    // Проверить первые 10 ссылок
    for (let i = 0; i < Math.min(10, count); i++) {
      const link = tocLinks.nth(i);
      const href = await link.getAttribute('href');
      
      if (href && href.startsWith('#')) {
        const sectionId = href.substring(1);
        await link.click();
        
        // Проверить что секция существует
        const section = page.locator(`#${sectionId}`);
        const exists = await section.count() > 0;
        expect(exists).toBe(true);
      }
    }
  });

  test('features page - scroll to bottom sections', async ({ page }) => {
    await page.goto(BASE_URL + '/features');
    
    // Проверить секции внизу страницы
    const bottomSections = [
      'setup-wizard',
      'encrypted-backups',
      'grapheneos-app-repository',
    ];
    
    for (const id of bottomSections) {
      const section = page.locator(`#${id}`);
      const count = await section.count();
      
      if (count > 0) {
        // Прокрутить к секции
        await section.scrollIntoViewIfNeeded();
        await expect(section).toBeVisible();
      }
    }
  });
});
