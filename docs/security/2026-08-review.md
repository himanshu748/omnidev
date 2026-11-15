# OmniDev security and reliability review

Date: 2026-08-14

Repository: `himanshu748/omnidev`

Reviewed revision: `e795159c10d645ac87c02a8d53bbe293c103f16f` plus the local remediation diff

## Outcome

The default local-only deployment is materially safer after this review. One
fresh-install blocker and six security weaknesses were fixed. No known
vulnerabilities were reported for the exact locked Python dependency set, no
actionable high/medium Bandit findings remain, and all backend and native build
checks pass.

This is not a claim of absolute safety. Two meaningful residual risks remain:
release artifacts are unsigned/unnotarized, and enabled third-party MCP servers
are not isolated by an operating-system sandbox.

## Remediated findings

### OD-001 — High — Fresh installs selected an incompatible MCP major

- **Location:** `backend/requirements.txt:11`, `backend/requirements.lock`
- **Impact:** The unconstrained `mcp` requirement selected MCP 2, which removed
  `mcp.server.fastmcp`; a clean install failed during test collection and the
  backend could not start.
- **Fix:** Constrained the existing API to `mcp>=1.28,<2`, generated a fully
  hashed lockfile, and made local setup, app bootstrap, CI, and MCP setup consume
  that lock with `--require-hashes`.
- **Evidence:** A locked dry-run resolved successfully to MCP 1.29.0. The MCP
  project describes v2 as a breaking release and recommends the v1 line for
  production while migration is pending: <https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/get-started/installation.md>.

### OD-002 — High — “Always Allow” approved more than the displayed action

- **Location:** `backend/app/services/agent_service.py:114`
- **Impact:** Approval keys previously covered only a command's first argument
  or a file's parent directory. Approving one harmless action could silently
  authorize different code, content, paths, or MCP arguments later in the task.
- **Fix:** Approval reuse now requires the exact tool and canonicalized complete
  argument object. The macOS UI and command warning explain that exact scope and
  the permissions inherited by executed code.

### OD-003 — High — Writable third-party MCP tools were available without per-call approval

- **Location:** `backend/app/services/mcp_client_service.py:49`, `:248`, `:322`, `:372`
- **Impact:** Normal tool chat has no approval sheet but previously exposed
  filesystem, memory, and Git MCP servers. Runtime package versions also floated,
  and child processes inherited the user's real home path.
- **Fix:** Normal chat now receives only catalog entries marked read-only.
  Writable MCP tools remain available only in Agent mode, which approves every
  external tool invocation. Curated server versions are exact, their existence
  was checked against npm/PyPI, and child processes receive a private isolated
  `HOME` plus a minimal `PATH`/`HOME` environment.

### OD-004 — Medium — Private/metadata proxy targets bypassed the SSRF policy

- **Location:** `backend/app/services/url_guard.py:171`
- **Impact:** A public destination could be fetched through a user-supplied proxy
  on localhost, a private LAN address, or a cloud metadata address.
- **Fix:** Proxy hostnames now use the same private/reserved address block policy
  as destination URLs. Regression cases cover loopback, RFC1918, and metadata IPs.

### OD-005 — Medium — Sensitive local state did not consistently enforce owner-only permissions

- **Location:** `backend/app/services/data_paths.py:11`, `:22`, `:44`
- **Impact:** Chat history, indexed plaintext excerpts, configured workspace
  paths, and MCP state could depend on the user's umask.
- **Fix:** Data directories are `0700`; databases, WAL/SHM files, and JSON state
  are `0600`. Private writes refuse symlinks where the platform supports
  `O_NOFOLLOW`, and private subdirectories cannot escape `DATA_DIR`.

### OD-006 — Medium — Vision uploads were fully buffered before size rejection

- **Location:** `backend/app/routers/vision.py:15`, `:41`
- **Impact:** An oversized multipart body could consume substantially more than
  the documented 10 MB image limit before being rejected. Prompts were also
  unbounded.
- **Fix:** Image data is read in 1 MB chunks and stopped at 10 MB; prompts are
  limited to 4,000 characters.

### OD-007 — Medium — CI/release dependencies were mutable and installs were not reproducible

- **Location:** `.github/workflows/ci.yml:21`, `.github/workflows/release.yml:14`,
  `backend/requirements.lock`
- **Impact:** Moving GitHub Action tags and unconstrained transitive Python
  packages increased build-time supply-chain risk.
- **Fix:** GitHub Actions are pinned to full commit SHAs. Python installs use an
  exact, hashed cross-platform lock. Release workflows now publish SHA-256 sums
  and no longer recommend removing quarantine with `xattr`.

## Residual risks

### OD-R01 — Medium — Releases are unsigned and not notarized

- **Location:** `README.md:175`, `.github/workflows/release.yml:41`,
  `scripts/macos/build-app.sh:110`
- **Current mitigation:** SHA-256 sums are published and documentation is explicit
  that they detect corruption but do not authenticate the publisher. Source builds
  remain available.
- **Required closure:** Add an Apple Developer ID Application certificate,
  hardened-runtime signing, notarization, and stapling in the protected release
  workflow. This needs owner-controlled Apple credentials and cannot be completed
  safely from repository code alone.

### OD-R02 — Medium — MCP processes have the user's OS privileges

- **Location:** `backend/app/services/mcp_client_service.py:248`
- **Current mitigation:** Curated exact top-level packages, isolated `HOME`, minimal
  environment, read-only filtering in normal chat, and exact per-call approval for
  writable tools in Agent mode.
- **Required closure:** Run third-party MCP processes inside a real macOS sandbox
  or a separate low-privilege account/container. Exact top-level versions do not
  freeze every registry-resolved transitive dependency.

### OD-R03 — Low — Explicit remote mode remains unauthenticated

- **Location:** `backend/app/config.py:73`, `backend/app/main.py:115`
- **Current mitigation:** Remote clients are denied by default and the API is
  intended for loopback only.
- **Operational rule:** Keep `ALLOW_REMOTE_CLIENTS=0`. If remote access becomes a
  product requirement, add authentication and TLS before enabling it.

## Verification performed

- Backend: `337 passed` (one dependency warning; no failures).
- Native macOS package: `swift build --disable-sandbox -c debug` completed.
- Python advisories: `pip-audit` reported no known vulnerabilities for every
  exact package in `backend/requirements.lock`.
- Static security scan: Bandit reported no actionable high/medium issues. One
  dynamic SQL construction was manually verified to interpolate only generated
  `?` placeholders while all values remain bound parameters.
- Secrets: the tracked-tree scan found no credential patterns. A separate scan of
  all 73 Git revisions found only deliberate fake private-key headers used by
  secret-filter tests/probes; no credential material was present. Bespoke secret
  formats remain outside pattern-based scan coverage.
- Dependency/package integrity: hash-enforced pip dry-run passed; all six exact MCP
  runtime package versions exist in their respective public registries.
- Scripts/workflows: shell syntax, YAML parsing, and `git diff --check` passed.

## Release guidance

Keep these changes under the repository's normal review and protected-branch
controls. Do not describe a macOS release as authenticated or fully trusted
until OD-R01 is closed.
