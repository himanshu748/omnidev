import { test, expect } from "@playwright/test";
import { mockApiError, mockJson } from "./helpers";

test("devops command flow", async ({ page }) => {
  await mockJson(page, "**/api/devops/command", {
    action: "list_ec2",
    params: {},
    raw_result: { count: 1, instances: [{ id: "i-1" }] },
    summary: "Found 1 instance",
    needs_confirmation: false,
  });
  await page.goto("/devops");
  await page.fill("#devops-message", "List my EC2 instances");
  await page.getByRole("button", { name: "Run Command" }).click();
  await expect(page.getByText("Recent Operations")).toBeVisible();
  await expect(page.getByText("list_ec2")).toBeVisible();
  await expect(page.getByText("Found 1 instance")).toBeVisible();
});

test("devops error handling", async ({ page }) => {
  await mockApiError(page, "**/api/devops/command", 500, "Boom");
  await page.goto("/devops");
  await page.fill("#devops-message", "List my EC2 instances");
  await page.getByRole("button", { name: "Run Command" }).click();
  await expect(page.getByText("ERROR")).toBeVisible();
  await expect(page.getByText("Boom")).toBeVisible();
});
