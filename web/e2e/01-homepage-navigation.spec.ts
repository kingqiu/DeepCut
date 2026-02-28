import { test, expect } from '@playwright/test';

test.describe('模块 1: 首页 - 导航与布局', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('1.1 页面成功加载，显示基础元素', async ({ page }) => {
    // 检查标题
    await expect(page.locator('h1')).toContainText('DeepCut');
    
    // 检查副标题
    await expect(page.locator('text=智能短视频切片')).toBeVisible();
    
    // 检查 Settings 图标
    const settingsLink = page.locator('a[aria-label="设置"]');
    await expect(settingsLink).toBeVisible();
    
    // 检查新建切片任务标题
    await expect(page.locator('text=新建切片任务')).toBeVisible();
  });

  test('1.2 点击 Settings 图标跳转到设置页', async ({ page }) => {
    const settingsLink = page.locator('a[aria-label="设置"]');
    await settingsLink.click();
    
    // 验证 URL 变化
    await expect(page).toHaveURL('/settings');
    
    // 验证设置页标题
    await expect(page.locator('h1')).toContainText('设置');
  });

  test('1.3 从设置页返回首页', async ({ page }) => {
    // 先跳转到设置页
    await page.goto('/settings');
    
    // 点击返回按钮
    const backButton = page.locator('button:has-text("返回")');
    await backButton.click();
    
    // 验证回到首页
    await expect(page).toHaveURL('/');
    await expect(page.locator('h1')).toContainText('DeepCut');
  });

  test('1.4 Tab 切换功能', async ({ page }) => {
    // 默认应该在"按项目" Tab
    const projectsTab = page.locator('button[role="tab"]:has-text("按项目")');
    await expect(projectsTab).toHaveAttribute('data-state', 'active');
    
    // 切换到"全局片段库" Tab
    const clipsTab = page.locator('button[role="tab"]:has-text("全局片段库")');
    await clipsTab.click();
    
    // 验证 Tab 状态变化
    await expect(clipsTab).toHaveAttribute('data-state', 'active');
    await expect(projectsTab).toHaveAttribute('data-state', 'inactive');
    
    // 验证内容区域变化（应该显示搜索框）
    await expect(page.locator('input[placeholder*="搜索"]')).toBeVisible();
  });

  test('1.5 上传区域显示正确', async ({ page }) => {
    // 检查文件上传 Tab
    const uploadTab = page.locator('button[role="tab"]:has-text("文件上传")');
    await expect(uploadTab).toBeVisible();
    
    // 检查本地路径 Tab
    const localTab = page.locator('button[role="tab"]:has-text("本地路径")');
    await expect(localTab).toBeVisible();
    
    // 默认应该在文件上传 Tab
    await expect(uploadTab).toHaveAttribute('data-state', 'active');
    
    // 检查上传提示文本
    await expect(page.locator('text=拖拽视频文件到这里，或点击选择')).toBeVisible();
  });
});
