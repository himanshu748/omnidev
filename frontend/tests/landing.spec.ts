import { test, expect } from "@playwright/test";

test("landing page navigation", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "OmniDev runs on your machine first." })).toBeVisible();
  await expect(page.getByText("Local API target")).toBeVisible();
  await expect(page.getByText("http://localhost:8000").first()).toBeVisible();
  await page.getByRole("link", { name: "DevOps Agent" }).first().click();
  await expect(page).toHaveURL(/\/devops/);
  await expect(page.getByRole("heading", { name: "DevOps Agent", exact: true })).toBeVisible();
});
