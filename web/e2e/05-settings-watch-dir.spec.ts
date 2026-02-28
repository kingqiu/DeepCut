import { test, expect } from '@playwright/test';

test.describe('模块 9: 设置页 - 本地目录监听', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
  });

  test('9.1 设置页面加载', async ({ page }) => {
    // 检查页面标题
    await expect(page.locator('h1')).toContainText('设置');
    
    // 检查返回按钮
    await expect(page.locator('button:has-text("返回")')).toBeVisible();
    
    // 检查本地目录监听标题
    await expect(page.locator('h2:has-text("本地目录监听")')).toBeVisible();
    
    // 检查说明文本
    await expect(page.locator('text=配置本地视频目录')).toBeVisible();
  });

  test('9.2 添加目录输入框显示', async ({ page }) => {
    // 检查路径输入框
    const pathInput = page.locator('input[name="watchPath"]');
    await expect(pathInput).toBeVisible();
    await expect(pathInput).toHaveAttribute('placeholder', '/path/to/video/directory');
    
    // 检查间隔输入框
    const intervalInput = page.locator('input[name="scanInterval"]');
    await expect(intervalInput).toBeVisible();
    await expect(intervalInput).toHaveAttribute('aria-label', '扫描间隔（秒）');
    
    // 检查添加按钮
    const addButton = page.locator('button').filter({ has: page.locator('svg') }).first();
    await expect(addButton).toBeVisible();
  });

  test('9.3 输入框有正确的属性', async ({ page }) => {
    const pathInput = page.locator('input[name="watchPath"]');
    const intervalInput = page.locator('input[name="scanInterval"]');
    
    // 检查 name 属性
    await expect(pathInput).toHaveAttribute('name', 'watchPath');
    await expect(intervalInput).toHaveAttribute('name', 'scanInterval');
    
    // 检查 autocomplete 属性
    await expect(pathInput).toHaveAttribute('autocomplete', 'off');
    
    // 检查 aria-label
    await expect(intervalInput).toHaveAttribute('aria-label', '扫描间隔（秒）');
  });

  test('9.4 默认间隔值为 600 秒', async ({ page }) => {
    const intervalInput = page.locator('input[name="scanInterval"]');
    await expect(intervalInput).toHaveValue('600');
  });

  test('9.5 空状态显示', async ({ page }) => {
    // 等待加载
    await page.waitForTimeout(1000);
    
    // 检查是否有目录列表或空状态
    const hasDirs = await page.locator('button[aria-label*="监听"]').count() > 0;
    const hasEmptyState = await page.locator('text=暂未配置监听目录').count() > 0;
    
    expect(hasDirs || hasEmptyState).toBeTruthy();
  });

  test('9.6 目录列表显示（如果有数据）', async ({ page }) => {
    await page.waitForTimeout(1000);
    
    const toggleButtons = page.locator('button[aria-label*="监听"]');
    const count = await toggleButtons.count();
    
    if (count > 0) {
      const firstButton = toggleButtons.first();
      
      // Toggle 按钮应该可见
      await expect(firstButton).toBeVisible();
      
      // 应该有 aria-label
      const ariaLabel = await firstButton.getAttribute('aria-label');
      expect(ariaLabel).toContain('监听');
      
      // 应该显示目录路径
      const dirPath = page.locator('.truncate').first();
      await expect(dirPath).toBeVisible();
    }
  });

  test('9.7 返回按钮功能', async ({ page }) => {
    const backButton = page.locator('button:has-text("返回")');
    await backButton.click();
    
    // 验证回到首页
    await expect(page).toHaveURL('/');
    await expect(page.locator('h1')).toContainText('DeepCut');
  });

  test('9.8 间隔下拉选择器显示（如果有目录）', async ({ page }) => {
    await page.waitForTimeout(1000);
    
    const selects = page.locator('select');
    const count = await selects.count();
    
    if (count > 0) {
      const firstSelect = selects.first();
      
      // 下拉选择器应该可见
      await expect(firstSelect).toBeVisible();
      
      // 应该有正确的样式类（包含 text-foreground）
      const classList = await firstSelect.getAttribute('class');
      expect(classList).toContain('text-foreground');
      
      // 应该有选项
      const options = firstSelect.locator('option');
      const optionCount = await options.count();
      expect(optionCount).toBeGreaterThan(0);
    }
  });
});
