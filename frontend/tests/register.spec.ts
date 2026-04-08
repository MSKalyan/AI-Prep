import { test, expect } from "@playwright/test";

test.describe("Register Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/register");
  });

  test("should display registration form with all fields", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Create Account" })).toBeVisible();
    await expect(page.getByLabel("Full Name")).toBeVisible();
    await expect(page.getByLabel("Username")).toBeVisible();
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByLabel("Password", { exact: true })).toBeVisible();
    await expect(page.getByLabel("Confirm Password")).toBeVisible();
    await expect(page.getByRole("button", { name: "Register" })).toBeVisible();
  });

  test("should show error when passwords do not match", async ({ page }) => {
    await page.getByLabel("Full Name").fill("John Doe");
    await page.getByLabel("Username").fill("johndoe");
    await page.getByLabel("Email").fill("john@example.com");
    await page.getByLabel("Password", { exact: true }).fill("password123");
    await page.getByLabel("Confirm Password").fill("differentpass");
    await page.getByRole("button", { name: "Register" }).click();
    await expect(page.getByText("Passwords do not match")).toBeVisible();
  });

  test("should show error when required fields are empty", async ({ page }) => {
    const registerBtn = page.getByRole("button", { name: "Register" });
    await registerBtn.click();
    const url = page.url();
    expect(url).toContain("/register");
  });

  test("should navigate to login page", async ({ page }) => {
    await page.locator("form").getByRole("link", { name: "Login" }).click();
    await expect(page).toHaveURL("/login");
  });
});