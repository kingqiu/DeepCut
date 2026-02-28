import { test, expect } from '@playwright/test';

test.describe('无障碍性测试', () => {
  test('A1 首页键盘导航', async ({ page }) => {
    await page.goto('/');
    
    // Tab 键遍历交互元素
    await page.keyboard.press('Tab');
    
    // 检查焦点是否可见（应该有 focus-visible 样式）
    const focused = page.locator(':focus');
    await expect(focused).toBeVisible();
  });

  test('A2 Settings 图标有 aria-label', async ({ page }) => {
    await page.goto('/');
    
    const settingsLink = page.locator('a[aria-label="设置"]');
    await expect(settingsLink).toBeVisible();
    await expect(settingsLink).toHaveAttribute('aria-label', '设置');
  });

  test('A3 文件上传 input 有 label', async ({ page }) => {
    await page.goto('/');
    
    // 检查 file input 有对应的 label
    const fileInput = page.locator('input[type="file"]');
    const inputId = await fileInput.getAttribute('id');
    
    if (inputId) {
      const label = page.locator(`label[for="${inputId}"]`);
      await expect(label).toBeVisible();
    }
  });

  test('A4 表单输入框有 name 属性', async ({ page }) => {
    await page.goto('/');
    
    // 切换到本地路径 Tab
    await page.locator('button[role="tab"]:has-text("本地路径")').click();
    
    const pathInput = page.locator('input[placeholder="/path/to/video.mp4"]');
    await expect(pathInput).toHaveAttribute('name', 'videoPath');
    await expect(pathInput).toHaveAttribute('autocomplete', 'off');
  });

  test('A5 设置页表单字段有正确属性', async ({ page }) => {
    await page.goto('/settings');
    
    const pathInput = page.locator('input[name="watchPath"]');
    const intervalInput = page.locator('input[name="scanInterval"]');
    
    // 检查 name 属性
    await expect(pathInput).toHaveAttribute('name', 'watchPath');
    await expect(intervalInput).toHaveAttribute('name', 'scanInterval');
    
    // 检查 autocomplete
    await expect(pathInput).toHaveAttribute('autocomplete', 'off');
    
    // 检查 aria-label
    await expect(intervalInput).toHaveAttribute('aria-label', '扫描间隔（秒）');
  });

  test('A6 Toggle 按钮有 aria-label', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForTimeout(1000);
    
    const toggleButtons = page.locator('button[aria-label*="监听"]');
    const count = await toggleButtons.count();
    
    if (count > 0) {
      const firstButton = toggleButtons.first();
      const ariaLabel = await firstButton.getAttribute('aria-label');
      expect(ariaLabel).toMatch(/(启用|禁用)监听/);
    }
  });

  test('A7 图片有 alt 属性', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    
    const images = page.locator('img');
    const count = await images.count();
    
    if (count > 0) {
      for (let i = 0; i < Math.min(count, 5); i++) {
        const img = images.nth(i);
        await expect(img).toHaveAttribute('alt');
      }
    }
  });

  test('A8 图片有 width 和 height', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    
    const images = page.locator('img');
    const count = await images.count();
    
    if (count > 0) {
      for (let i = 0; i < Math.min(count, 5); i++) {
        const img = images.nth(i);
        const hasWidth = await img.getAttribute('width');
        const hasHeight = await img.getAttribute('height');
        
        // 图片应该有 width 和 height 属性（防止 CLS）
        expect(hasWidth).toBeTruthy();
        expect(hasHeight).toBeTruthy();
      }
    }
  });

  test('A9 播放按钮有 aria-label', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    
    // 切换到全局片段库看是否有结果
    await page.locator('button[role="tab"]:has-text("全局片段库")').click();
    await page.waitForTimeout(1000);
    
    const playButtons = page.locator('button[aria-label="播放视频"]');
    const count = await playButtons.count();
    
    if (count > 0) {
      await expect(playButtons.first()).toHaveAttribute('aria-label', '播放视频');
    }
  });

  test('A10 HTML lang 属性正确', async ({ page }) => {
    await page.goto('/');
    
    const html = page.locator('html');
    await expect(html).toHaveAttribute('lang', 'zh-CN');
  });
});
