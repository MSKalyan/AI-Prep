import { test, expect } from '@playwright/test';

test.describe('Form Validation', () => {
  test.describe('Login Form Validation', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/login');
    });

    test('should show error for invalid email format', async ({ page }) => {
      await page.getByLabel('Email').fill('notanemail');
      await page.getByLabel('Password').fill('password123');
      await page.getByRole('button', { name: 'Login' }).click();
    });

    test('should handle empty form submission', async ({ page }) => {
      await page.getByRole('button', { name: 'Login' }).click();
      await expect(page.getByText('Email is required')).toBeVisible();
    });

    test('should display error message when submitted without email', async ({ page }) => {
      await page.getByLabel('Password').fill('password123');
      await page.getByRole('button', { name: 'Login' }).click();
      await expect(page.getByText('Email is required')).toBeVisible();
    });
  });

  test.describe('Register Form Validation', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/register');
    });

    test('should validate password confirmation', async ({ page }) => {
      await page.getByLabel('Full Name').fill('Test User');
      await page.getByLabel('Username').fill('testuser');
      await page.getByLabel('Email').fill('test@example.com');
      await page.getByLabel('Password', { exact: true }).fill('password123');
      await page.getByLabel('Confirm Password').fill('wrongpassword');
      await page.getByRole('button', { name: 'Register' }).click();
      await expect(page.getByText('Passwords do not match')).toBeVisible();
    });

    test('should display error when passwords do not match', async ({ page }) => {
      await page.getByLabel('Full Name').fill('Test User');
      await page.getByLabel('Username').fill('testuser');
      await page.getByLabel('Email').fill('test@example.com');
      await page.getByLabel('Password', { exact: true }).fill('password123');
      await page.getByLabel('Confirm Password').fill('wrongpassword');
      await page.getByRole('button', { name: 'Register' }).click();
      await expect(page.getByText('Passwords do not match')).toBeVisible();
    });
  });
});
