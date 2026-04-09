import { test, expect } from "@playwright/test";

test.describe("Profile Page", () => {
  test("should load profile page without crashing (no auth redirect)", async ({ page }) => {
    await page.goto("/profile");
    await expect(page).toHaveURL("/profile");
  });
});

test.describe("Roadmaps Page", () => {
  test("should load roadmaps page without crashing (no auth redirect)", async ({ page }) => {
    await page.goto("/dashboard/roadmaps");
    await expect(page).toHaveURL("/dashboard/roadmaps");
  });
});
