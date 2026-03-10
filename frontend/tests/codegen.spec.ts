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
  await expect(page.getByText("Generated project")).toBeVisible();
  await expect(page.getByText("package.json")).toBeVisible();
});
