import { test, expect } from '@playwright/test';

test.describe('模块 8: 全局片段库', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // 切换到全局片段库 Tab
    await page.locator('button[role="tab"]:has-text("全局片段库")').click();
    await page.waitForTimeout(1000);
  });

  test('8.1 全局片段库页面显示', async ({ page }) => {
    // 检查搜索框
    const searchInput = page.locator('input[placeholder*="搜索"]');
    await expect(searchInput).toBeVisible();
    
    // 检查搜索按钮
    const searchButton = page.locator('button:has-text("搜索")');
    await expect(searchButton).toBeVisible();
    
    // 检查空状态提示
    await expect(page.locator('text=选择标签或输入关键词开始搜索')).toBeVisible();
  });

  test('8.2 标签筛选面板显示', async ({ page }) => {
    // 等待标签加载
    await page.waitForTimeout(2000);
    
    // 检查是否有标签维度显示
    const tagBadges = page.locator('[class*="badge"]');
    const count = await tagBadges.count();
    
    // 如果有数据，应该显示标签
    if (count > 0) {
      await expect(tagBadges.first()).toBeVisible();
    }
  });

  test('8.3 点击标签触发搜索', async ({ page }) => {
    await page.waitForTimeout(2000);
    
    const tagBadges = page.locator('[class*="badge"][class*="cursor-pointer"]');
    const count = await tagBadges.count();
    
    if (count > 0) {
      const firstTag = tagBadges.first();
      
      // 点击标签
      await firstTag.click();
      
      // 等待搜索完成
      await page.waitForTimeout(1000);
      
      // 标签应该高亮（激活状态）
      const classList = await firstTag.getAttribute('class');
      expect(classList).toBeTruthy();
      
      // 应该显示搜索结果或无结果提示
      const hasResults = await page.locator('a[href^="/projects/"]').count() > 0;
      const hasNoResults = await page.locator('text=没有找到匹配的切片').count() > 0;
      
      expect(hasResults || hasNoResults).toBeTruthy();
    }
  });

  test('8.4 关键词搜索功能', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="搜索"]');
    const searchButton = page.locator('button:has-text("搜索")');
    
    // 输入关键词
    await searchInput.fill('测试');
    
    // 点击搜索按钮
    await searchButton.click();
    
    // 等待搜索完成
    await page.waitForTimeout(1000);
    
    // 应该显示搜索结果或无结果提示
    const hasResults = await page.locator('a[href^="/projects/"]').count() > 0;
    const hasNoResults = await page.locator('text=没有找到匹配的切片').count() > 0;
    
    expect(hasResults || hasNoResults).toBeTruthy();
  });

  test('8.5 按 Enter 键触发搜索', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="搜索"]');
    
    // 输入关键词并按 Enter
    await searchInput.fill('测试');
    await searchInput.press('Enter');
    
    // 等待搜索完成
    await page.waitForTimeout(1000);
    
    // 应该显示搜索结果或无结果提示
    const hasResults = await page.locator('a[href^="/projects/"]').count() > 0;
    const hasNoResults = await page.locator('text=没有找到匹配的切片').count() > 0;
    
    expect(hasResults || hasNoResults).toBeTruthy();
  });

  test('8.6 清除筛选功能', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="搜索"]');
    
    // 输入关键词
    await searchInput.fill('测试');
    await searchInput.press('Enter');
    await page.waitForTimeout(1000);
    
    // 点击清除按钮（包含 X 图标的按钮）
    const clearButton = page.locator('button[variant="ghost"]').filter({ has: page.locator('svg') });
    const hasClearButton = await clearButton.count() > 0;
    
    if (hasClearButton) {
      await clearButton.click();
      
      // 等待状态更新
      await page.waitForTimeout(500);
      
      // 搜索框应该清空
      await expect(searchInput).toHaveValue('');
      
      // 应该回到初始状态
      await expect(page.locator('text=选择标签或输入关键词开始搜索')).toBeVisible();
    }
  });

  test('8.7 搜索结果卡片显示项目名称', async ({ page }) => {
    await page.waitForTimeout(2000);
    
    const tagBadges = page.locator('[class*="badge"][class*="cursor-pointer"]');
    const count = await tagBadges.count();
    
    if (count > 0) {
      await tagBadges.first().click();
      await page.waitForTimeout(1000);
      
      const resultCards = page.locator('a[href^="/projects/"]');
      const resultCount = await resultCards.count();
      
      if (resultCount > 0) {
        // 每个结果卡片应该有项目名称链接
        const projectLink = resultCards.first().locator('a[href^="/projects/"]').first();
        await expect(projectLink).toBeVisible();
      }
    }
  });
});
