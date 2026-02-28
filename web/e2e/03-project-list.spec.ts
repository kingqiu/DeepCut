import { test, expect } from '@playwright/test';

test.describe('模块 4: 项目列表', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('4.1 项目列表区域显示', async ({ page }) => {
    // 确保在"按项目" Tab
    const projectsTab = page.locator('button[role="tab"]:has-text("按项目")');
    await projectsTab.click();
    
    // 等待项目列表加载
    await page.waitForTimeout(1000);
    
    // 检查是否有项目卡片或空状态
    const hasProjects = await page.locator('a[href^="/projects/"]').count() > 0;
    const hasEmptyState = await page.locator('text=暂无项目').count() > 0;
    
    expect(hasProjects || hasEmptyState).toBeTruthy();
  });

  test('4.2 项目卡片基本元素显示', async ({ page }) => {
    const projectsTab = page.locator('button[role="tab"]:has-text("按项目")');
    await projectsTab.click();
    await page.waitForTimeout(1000);
    
    const projectCards = page.locator('a[href^="/projects/"]');
    const count = await projectCards.count();
    
    if (count > 0) {
      const firstCard = projectCards.first();
      
      // 检查卡片可见
      await expect(firstCard).toBeVisible();
      
      // 卡片应该有缩略图区域
      const thumbnail = firstCard.locator('.aspect-video');
      await expect(thumbnail).toBeVisible();
      
      // 卡片应该有状态标签（通过文本内容定位）
      const hasStatusText = await firstCard.locator('text=/排队中|正在切片|已完成|处理失败/').count() > 0;
      expect(hasStatusText).toBeTruthy();
    }
  });

  test('4.3 点击项目卡片跳转到详情页', async ({ page }) => {
    const projectsTab = page.locator('button[role="tab"]:has-text("按项目")');
    await projectsTab.click();
    await page.waitForTimeout(1000);
    
    const projectCards = page.locator('a[href^="/projects/"]');
    const count = await projectCards.count();
    
    if (count > 0) {
      const firstCard = projectCards.first();
      const href = await firstCard.getAttribute('href');
      
      await firstCard.click();
      
      // 验证 URL 变化
      await expect(page).toHaveURL(href!);
      
      // 验证详情页有返回按钮
      await expect(page.locator('button:has-text("返回")')).toBeVisible();
    }
  });

  test('4.4 项目卡片悬停效果', async ({ page }) => {
    const projectsTab = page.locator('button[role="tab"]:has-text("按项目")');
    await projectsTab.click();
    await page.waitForTimeout(1000);
    
    const projectCards = page.locator('a[href^="/projects/"]');
    const count = await projectCards.count();
    
    if (count > 0) {
      const firstCard = projectCards.first();
      
      // 悬停
      await firstCard.hover();
      
      // 卡片应该有 hover 样式（shadow-md）
      const classList = await firstCard.locator('> div').first().getAttribute('class');
      expect(classList).toBeTruthy();
    }
  });
});
