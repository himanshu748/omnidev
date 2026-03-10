import { test, expect } from "@playwright/test";
import { mockJson } from "./helpers";

test("vision analyze flow", async ({ page }) => {
  await mockJson(page, "**/api/vision/analyze", {
    mode: "analyze",
    result: "Detected a sample image",
    model: "test-model",
    tokens_used: 42,
  });
  await page.goto("/vision");
  await page.setInputFiles("#vision-file", {
    name: "sample.png",
    mimeType: "image/png",
    buffer: Buffer.from("sample"),
  });
  await page.getByRole("button", { name: "🔮 Analyze Image" }).click();
  await expect(page.getByText("Detected a sample image")).toBeVisible();
  await expect(page.getByText("test-model")).toBeVisible();
});
