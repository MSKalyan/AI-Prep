import { test, expect } from '@playwright/test';

test.describe('Accessibility', () => {
  test('login page should have accessible form labels', async ({ page }) => {
    await page.goto('/login');

    const emailInput = page.getByLabel('Email');
    const passwordInput = page.getByLabel('Password');
    const loginButton = page.getByRole('button', { name: 'Login' });

    await expect(emailInput).toHaveAttribute('type', 'email');
    await expect(passwordInput).toHaveAttribute('type', 'password');
    await expect(loginButton).toBeEnabled();
  });

  test('register page should have accessible form labels', async ({ page }) => {
    await page.goto('/register');

    const fullNameInput = page.getByLabel('Full Name');
    const usernameInput = page.getByLabel('Username');
    const emailInput = page.getByLabel('Email');
    const passwordInput = page.getByLabel('Password', { exact: true });
    const confirmPasswordInput = page.getByLabel('Confirm Password');
    const registerButton = page.getByRole('button', { name: 'Register' });

    await expect(fullNameInput).toBeVisible();
    await expect(usernameInput).toBeVisible();
    await expect(emailInput).toHaveAttribute('type', 'email');
    await expect(passwordInput).toHaveAttribute('type', 'password');
    await expect(confirmPasswordInput).toHaveAttribute('type', 'password');
    await expect(registerButton).toBeEnabled();
  });

  test('login page should be keyboard navigable', async ({ page }) => {
    await page.goto('/login');

    await page.locator("input[type='email']").focus();
    await expect(page.locator("input[type='email']")).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator("input[type='password']")).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: 'Login' })).toBeFocused();
  });

  test('register page should be keyboard navigable', async ({ page }) => {
    await page.goto('/register');

    await page.locator('input#full_name').focus();
    await expect(page.locator('input#full_name')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('input#username')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('input#email')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('input#password')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('input#password_confirm')).toBeFocused();
  });
});
