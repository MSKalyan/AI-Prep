import { test, expect } from "@playwright/test";

test.describe("Login Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
  });

  test("should display login form with all elements", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Login" })).toBeVisible();
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
    await expect(page.getByRole("button", { name: "Login" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Create account" })).toBeVisible();
  });

  test("should show error when email is empty", async ({ page }) => {
    await page.getByLabel("Password").fill("password123");
    await page.getByRole("button", { name: "Login" }).click();
    await expect(page.getByText("Email is required")).toBeVisible();
  });

  test("should show error when password is empty", async ({ page }) => {
    await page.getByLabel("Email").fill("test@example.com");
    await page.getByRole("button", { name: "Login" }).click();
    await expect(page.getByText("Password is required")).toBeVisible();
  });

  test("should navigate to register page", async ({ page }) => {
    await page.getByRole("link", { name: "Create account" }).click();
    await expect(page).toHaveURL("/register");
  });
});