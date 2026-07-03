# Claude For Open Source Application Draft

Program link: https://claude.com/contact-sales/claude-for-oss

Prepared for: Himanshu Kumar (`himanshu748`)

GitHub profile: https://github.com/himanshu748

Primary project: https://github.com/himanshu748/omnidev

## Program Notes

Verified from the Claude for Open Source page on June 18, 2026:

- Applications are reviewed on a rolling basis.
- The program accepts up to 10,000 contributors.
- Approved applicants receive 6 months of Claude Max 20x.
- The page primarily calls out maintainers of public repos with 5,000+ GitHub stars or 1M+ monthly npm downloads, but it also says maintainers of ecosystem-critical projects should apply even if they do not fit that exact threshold.

This draft positions the application as a student, OSS contributor, and emerging maintainer application: multiple merged PRs across developer ecosystem repos, and OmniDev as the new local-first developer ecosystem project.

## Fields To Confirm Before Submitting

- Preferred contact email.
- Exact name to use on the form.
- Whether to mention the GitHub email from local git config or a different public email.
- Any X/Twitter, LinkedIn, website, or portfolio link you want included.
- Whether you want to submit as "OSS contributor", "maintainer", or "contributor and emerging maintainer" if the form asks.

## Short Application Answer

Use this if the form has a tight character limit.

> I am a student, OSS contributor, and emerging maintainer building OmniDev, a local-first AI developer workbench for the local developer ecosystem. I have multiple merged PRs across public developer tooling repos, including Google Gemini CLI, aden-hive/hive, OpenMetadata, Jenkins, and JetBrains/swot. OmniDev brings AI-assisted code generation, human-in-the-loop AWS operations through boto3, browser automation, vision analysis, and S3 management into one local FastAPI + Next.js cockpit. Claude Max and Claude Code would help me accelerate cross-platform desktop packaging for macOS, Windows, and Linux, improve tests and security reviews, write clearer docs, and make the project easier for local developers to adopt and contribute to.

## Longer Application Answer

Use this if the form asks why you should receive Claude for Open Source access.

> I am applying as a student, open-source contributor, and emerging maintainer. Over the last several months I have had multiple PRs merged across developer ecosystem repositories, including Google Gemini CLI, aden-hive/hive, OpenMetadata, Jenkins, JetBrains/swot, and my own OmniDev work. These PRs range from type-safety fixes and developer-tooling integrations to documentation and UI fixes in widely used projects.
>
> I am now building OmniDev: a local-first AI developer workbench for the local developer ecosystem. The goal is to give builders a polished cockpit that runs close to their machine and credentials, instead of forcing every workflow into remote dashboards. OmniDev currently combines a FastAPI backend and Next.js frontend for AI-assisted code generation, human-in-the-loop AWS DevOps actions using boto3, Playwright browser automation, visual analysis, and S3 storage management.
>
> The project direction is cross-platform and developer-friendly: local web app today, desktop app packaging for macOS, Windows, and Linux next. Agent mode is intentionally human-in-the-loop; risky AWS operations are parsed into explicit boto3 actions and require confirmation before execution. Code generation is also safety-scoped: the backend validates generated files and returns them for review, download, or isolated preview rather than executing generated projects server-side.
>
> Claude Max and Claude Code would directly help me turn OmniDev into a stronger OSS project: hardening the backend, improving test coverage, reviewing security boundaries around generated code and cloud operations, documenting setup for local developers, and building the cross-platform desktop packaging path. I would use the access to keep shipping public work, review issues and PRs faster, and make OmniDev useful to developers who want a local, inspectable, privacy-conscious AI workbench.

## Project Summary

> OmniDev is a local-first AI developer workbench that combines code generation, AWS DevOps automation, web scraping, vision analysis, and S3 management in one FastAPI + Next.js cockpit. It is designed for developers who want AI assistance without giving up local control of credentials, generated code, and infrastructure approvals.

## Ecosystem Impact

> OmniDev is aimed at the local developer ecosystem: solo builders, OSS contributors, and small teams who want AI-native workflows that still feel inspectable and safe. The project reduces setup friction by bundling common developer workflows into one local app, and it encourages safer agent use by keeping destructive operations human-confirmed and by keeping generated-code execution out of the backend.

## Why Claude

> Claude would be used for real OSS maintenance work: implementation planning, code review, documentation, tests, security reviews, issue triage, onboarding improvements, and desktop packaging across macOS, Windows, and Linux. The project benefits especially from Claude's strengths in large-codebase reasoning and careful refactoring because OmniDev spans frontend UX, FastAPI services, cloud SDK calls, and security-sensitive agent boundaries.

## Proof Of Work

GitHub search found 9 merged PRs authored by `himanshu748` across public repos. Focused checks found 3 merged PRs in upstream `aden-hive/hive`, 1 merged PR in `jenkinsci/json-api-plugin`, and 4 Hive-related merged PRs when including the separate `himanshu748/hive` repo.

- https://github.com/google-gemini/gemini-cli/pull/19881 - `fix(core): remove unsafe type assertion suppressions in error utils`, merged May 5, 2026.
- https://github.com/aden-hive/hive/pull/2862 - `feat: Antigravity IDE support for MCP servers and skills`, merged February 12, 2026.
- https://github.com/aden-hive/hive/pull/231 - `docs: update skills directory structure to match actual output`.
- https://github.com/aden-hive/hive/pull/228 - `fix: remove duplicate web_search tool registration`.
- https://github.com/open-metadata/OpenMetadata/pull/27509 - `fix: resolve dashboard card layout broken by long translations in Russian locale`.
- https://github.com/JetBrains/swot/pull/37610 - `Add khwaja Moinuddin Chishti Language University`.
- https://github.com/jenkinsci/json-api-plugin/pull/107 - `docs: correct spelling of JSON API in plugin title`.
- https://github.com/himanshu748/omnidev/pull/2 - `docs: clarify provider modes and mark external AI/cloud integrations as optional`.
- https://github.com/himanshu748/hive/pull/5 - `docs: add proper markdown header to ROADMAP.md` in a separate Hive-related repo.

Current OmniDev proof points:

- Public repo: https://github.com/himanshu748/omnidev
- Local-first FastAPI + Next.js architecture.
- Backend test suite passes locally: 58 tests.
- Frontend typecheck and production build pass locally.
- Live local probes pass for health, scraper, preview, and S3 listing through the local AWS credential chain.
- Human-in-the-loop DevOps design with explicit confirmation for destructive AWS actions.
- Code generation is generation-only on the backend and blocks risky file/script outputs.

## Suggested Submitted Links

- GitHub profile: https://github.com/himanshu748
- OmniDev repo: https://github.com/himanshu748/omnidev
- Gemini CLI merged PR: https://github.com/google-gemini/gemini-cli/pull/19881
- Hive merged PRs:
  - https://github.com/aden-hive/hive/pull/2862
  - https://github.com/aden-hive/hive/pull/231
  - https://github.com/aden-hive/hive/pull/228
- Other ecosystem PRs:
  - https://github.com/open-metadata/OpenMetadata/pull/27509
  - https://github.com/jenkinsci/json-api-plugin/pull/107
  - https://github.com/JetBrains/swot/pull/37610

## Submission Checklist

- Open https://claude.com/contact-sales/claude-for-oss.
- Use `himanshu748` as the GitHub username/profile.
- Use OmniDev as the primary project being built now.
- Mention student status and multiple merged PRs across aden-hive/hive, Gemini CLI, OpenMetadata, Jenkins, and JetBrains/swot.
- Use the short or long answer above depending on the form limit.
- Add a personal email and any public social/profile links.
- Do not claim OmniDev is already a packaged desktop app; say it is local web app today and cross-platform desktop packaging is the next milestone.
