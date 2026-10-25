## Summary

<!-- What does this change and why? Link the issue: Closes #123 -->

## Type

- [ ] Bug fix
- [ ] Feature
- [ ] Docs
- [ ] Refactor / chore / CI
- [ ] Security hardening

## How was this tested?

<!-- Commands you ran, and manual steps. Add screenshots for UI changes. -->

## Checklist

- [ ] `make test` passes (backend pytest)
- [ ] `cd macos && swift build` passes (if Swift code changed)
- [ ] New behavior has tests, including the refusal path for any safety guard touched
- [ ] `docs/API.md` / README updated if endpoints or setup changed
- [ ] `CHANGELOG.md` `[Unreleased]` entry added if user-facing
- [ ] Keeps OmniDev local-first: works offline via Ollama, and no new data leaves the machine without an explicit opt-in
- [ ] PR title follows Conventional Commits (it becomes the squash commit)

## Notes

<!-- Tradeoffs, follow-ups, anything reviewers should look at closely -->
