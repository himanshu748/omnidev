import { test, expect } from "@playwright/test";
import { mockJson } from "./helpers";

test("codegen generate flow", async ({ page }) => {
  await mockJson(page, "**/api/codegen/generate", {
    files: [
      { path: "package.json", content: "{ }" },
      { path: "src/App.tsx", content: "export default function App() { return null; }" },
    ],
    instructions: "npm install && npm run dev",
  });
  await page.goto("/codegen");
  await page.fill("#codegen-prompt", "Build a todo app");
  await page.getByRole("button", { name: "Generate project" }).click();
  await expect(page.getByRole("heading", { name: "Live preview" })).toBeVisible();
  await expect(page.locator(".codegenFileListTitle", { hasText: "Files" })).toBeVisible();
  await expect(page.getByRole("button", { name: "package.json" })).toBeVisible();
});
