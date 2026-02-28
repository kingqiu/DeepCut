import { test, expect } from '@playwright/test';

test.describe('模块 3: 视频上传 - 本地路径提交', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // 切换到本地路径 Tab
    await page.locator('button[role="tab"]:has-text("本地路径")').click();
  });

  test('3.1 本地路径 Tab 显示正确', async ({ page }) => {
    // 检查说明文本
    await expect(page.locator('text=输入服务器上的视频文件绝对路径')).toBeVisible();
    
    // 检查输入框
    const input = page.locator('input[name="videoPath"]');
    await expect(input).toBeVisible();
    await expect(input).toHaveAttribute('placeholder', '/path/to/video.mp4');
    
    // 检查提交按钮
    const submitButton = page.locator('button:has-text("提交")');
    await expect(submitButton).toBeVisible();
    await expect(submitButton).toBeDisabled(); // 初始应该禁用
  });

  test('3.2 输入路径后提交按钮启用', async ({ page }) => {
    const input = page.locator('input[name="videoPath"]');
    const submitButton = page.locator('button:has-text("提交")');
    
    // 输入路径
    await input.fill('/test/video.mp4');
    
    // 提交按钮应该启用
    await expect(submitButton).toBeEnabled();
  });

  test('3.3 清空路径后提交按钮禁用', async ({ page }) => {
    const input = page.locator('input[name="videoPath"]');
    const submitButton = page.locator('button:has-text("提交")');
    
    // 输入路径
    await input.fill('/test/video.mp4');
    await expect(submitButton).toBeEnabled();
    
    // 清空路径
    await input.clear();
    
    // 提交按钮应该禁用
    await expect(submitButton).toBeDisabled();
  });

  test('3.4 按 Enter 键提交路径', async ({ page }) => {
    const input = page.locator('input[name="videoPath"]');
    
    // 输入路径并按 Enter
    await input.fill('/test/video.mp4');
    await input.press('Enter');
    
    // 应该显示提交中状态或成功/错误消息
    // 注意：这里会实际调用 API，可能失败（路径不存在）
    await page.waitForTimeout(1000);
    
    // 检查是否有消息显示（成功或错误）
    const hasMessage = await page.locator('div.rounded-md.px-3.py-2').count() > 0;
    expect(hasMessage).toBeTruthy();
  });

  test('3.5 表单字段有正确的属性', async ({ page }) => {
    const input = page.locator('input[name="videoPath"]');
    
    // 检查 name 属性
    await expect(input).toHaveAttribute('name', 'videoPath');
    
    // 检查 autocomplete 属性
    await expect(input).toHaveAttribute('autocomplete', 'off');
  });
});
