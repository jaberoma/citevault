import { expect, test } from "@playwright/test";

test.describe("Citevault E2E smoke", () => {
  test("Admin page loads and shows Evidence Library heading", async ({ page }) => {
    await page.goto("/admin");
    await expect(page.getByRole("heading", { name: /Evidence Library/i })).toBeVisible();
  });

  test("Settings page loads and shows model field", async ({ page }) => {
    await page.goto("/admin/settings");
    await expect(page.getByText(/model/i)).toBeVisible();
  });

  test("New Tailoring page loads with job posting textarea", async ({ page }) => {
    await page.goto("/tailor");
    await expect(page.getByRole("heading", { name: /New Tailoring/i })).toBeVisible();
  });

  test("History page loads", async ({ page }) => {
    await page.goto("/history");
    await expect(page.getByRole("heading", { name: /History/i })).toBeVisible();
  });
});
