# OmniDev PRD: v0.7.0 "Ask your whole Mac"

**Version:** 1.0 · 2026-07-14
**Owner:** himanshu748 · **Repo:** https://github.com/himanshu748/omnidev (local: `~/n/omnidev`)
**Status:** the brief for the release after agent mode. Written to be pasted into a fresh agent session with zero prior context.

**Release order:** v0.6.0 knowledge index (SHIPPED 2026-07-14, commit 9f5d8a4) → **v0.6.5 agent mode** (see `docs/PRD-v0.6.md` section 3) → **v0.7.0 whole-Mac RAG** (this document).

---

## 0. Critical environment notes

- The repo moved out of iCloud on 2026-07-14. It now lives at `~/n/omnidev` and builds and tests run **in place**, no /tmp scratch copy. Never move it back under `~/Documents` (iCloud quota is exhausted, writes wedge fileproviderd and reads of evicted files hang forever).
- Backend tests: `cd ~/n/omnidev/backend && python3 -m pytest` (255 passing as of v0.6.0).
- A running MCP server process does not pick up code changes; restart the session after editing `backend/app/mcp/`.
- Writing rule for all docs, commits and UI copy: no em or en dashes, no Oxford comma.

## 1. The goal

Today OmniDev answers questions about folders the user explicitly registers, and only for text-shaped files (md, txt, pdf, rst, html, plus code extensions). v0.7.0 makes the promise whole:

> Ask about anything on your Mac. A screenshot from three months ago, a PDF invoice, a Keynote deck, one specific file you point at. Fully offline.

Three distinct user intents, and they need three different mechanisms. Conflating them is the main design risk:

1. **"Search my Mac"** (broad recall): the indexed corpus. Needs scale, permissions and good filtering.
2. **"Read this file"** (ad-hoc, precise): attach a file or folder to one chat turn. Needs **no index at all**, and it is the cheapest high-value piece of this release.
3. **"What was in that screenshot?"** (visual recall): needs OCR, which the current pipeline has no path to.

## 2. Scale: measured, not assumed

Measured on the dev machine (2026-07-14) with Spotlight:

| Query | Count |
|---|---|
| All `public.content` under `~` | 455,178 |
| `public.content` under `~/Documents` | 201,523 |
| `public.content` under `~/n` | 54,818 |
| PDFs in Documents + Desktop + Downloads | 17 |
| Plain text in Documents + Desktop + Downloads | 3,458 |
| .docx in Documents + Desktop + Downloads | 3 |
| PNGs in Documents + Desktop + Downloads | 1,192 |

**The 455k number is a trap.** It is dominated by `node_modules`, `.venv`, caches and build output inside code repos. The actual user-document corpus on a real, heavily-used laptop is roughly **5,000 documents plus 1,200 screenshots**, which is about **20,000 to 30,000 chunks**, or roughly 80 to 120 MB of float32 vectors.

That is the release's central insight: **the filter matters far more than the index**. Get discovery right and laptop scale is comfortably tractable on a 16GB machine. Get it wrong and the first index never finishes.

Consequence: **discovery should come from Spotlight, not from `os.walk`.** macOS already maintains a filtered, incrementally-updated index of what is a real document. `_discover_files()` currently does a full `rglob` with a `stat` per file, which on a 200k-file tree costs minutes per source and rescans everything on every run.

## 3. What has to change in the v0.6.0 code

Two design choices that were correct for "a folder of docs" break at laptop scale.

### 3.1 Search holds the entire corpus in RAM, including text

`_load_matrix_sync()` loads **every chunk's embedding and its full text** into a Python list on every cache miss, and `_index_version` invalidates that cache after **every** indexing run. At 30k chunks that is roughly 120 MB of vectors plus 60 MB of Python strings rebuilt from SQLite each time anything changes. At 100k chunks it is a swap event on a 16GB machine, which is exactly the failure mode already documented in memory (12b generation collapsing to 0.4 tok/s under pressure).

**Fix:** keep vectors on disk and never hold chunk text in memory.

- Adopt **sqlite-vec** (deliberately skipped in v0.6.0 to avoid extension-loading risk across Pythons). Ship it as a wheel pinned in requirements, with a guarded fallback to the current numpy path when the extension fails to load, so a broken install degrades instead of crashing.
- Fetch `text` only for the final top-k rows, by chunk id, after ranking.
- Make cache invalidation incremental: a completed index job should append to the store, not force a full reload.

### 3.2 Retrieval is pure dense vector, which gets noisy at scale

Over 30k mixed-domain chunks, cosine-only retrieval starts surfacing topically-adjacent but useless chunks, and it cannot answer "the invoice from March" (a date filter) or an exact-token query like an error code or an order number.

**Fix:** hybrid retrieval.

- Add a **SQLite FTS5** virtual table over chunk text (built in, no new dependency) for BM25 keyword recall.
- Fuse dense and keyword result lists with **reciprocal rank fusion** (no tuning weights, robust default).
- Add metadata filters to `POST /api/knowledge/search`: `kind`, `after` / `before` on file mtime, `path_prefix`, `ext`. The chat grounding path should extract obvious date hints from the question and pass them through.

## 3.3 Hard blocker: iCloud-evicted files hang the indexer forever

Discovered while probing OCR on 2026-07-14, and it is the single most important correctness requirement in this release.

On a Mac with "Desktop & Documents" iCloud sync, files that have been evicted to the cloud are present in the filesystem listing but have no local data. **Opening one blocks indefinitely** when the file provider is unhealthy, at 0% CPU, with no timeout and no error. This is the exact failure that cost hours during the v0.6.0 release and forced the repo out of `~/Documents`. Measured on this machine: **19 of the screenshots sitting in `~/Desktop` are evicted**, and the first OCR probe against one hung until killed.

`~/Desktop` and `~/Documents` are precisely the folders this release invites users to add, so without a guard the flagship feature hangs on a large fraction of real Macs.

**Required guard**, verified working:

- `os.stat(path).st_flags & 0x40000000` (`SF_DATALESS`) identifies an evicted file. Confirmed: evicted screenshots report `flags=0x40000060`, a local file reports `0x00000000`.
- `stat` does **not** trigger materialization, so the check is free and safe. Only `open()` blocks.
- Discovery must skip dataless files rather than read them, record them as `skipped_evicted`, and the Knowledge page must show a count with a plain explanation ("N files are stored in iCloud and were skipped. Download them in Finder to include them.").
- Never call `brctl download` implicitly to materialize them. That silently consumes iCloud quota and disk, and on a full account it wedges.
- Belt and braces: wrap every extractor read in a worker with a hard timeout so any future stall degrades to a skipped file instead of a stuck index job.

## 4. New capability: screenshots and images

The headline feature, and the one with a clean macOS answer.

- **OCR via the Vision framework** (`VNRecognizeTextRequest`) through PyObjC (`pyobjc-framework-Vision` + `pyobjc-framework-Quartz`). On-device, free, no model download, and far more accurate than Tesseract on UI screenshots. OmniDev is macOS-only, so the platform dependency costs nothing.
- **Verified on the dev machine 2026-07-14** (probe kept at `docs/probes/ocr_probe.py`): PyObjC Vision is importable under the system python3, a synthetic invoice screenshot OCR'd correctly including the exact token `E_QUOTA_EXCEEDED` and the amount. Timing: **647 ms cold** (first call loads the models), **42 ms warm median** over 12 runs (min 40, max 45). Projected cost for the 1,200 screenshots on this machine: **under 1 minute single-threaded.**
- That measurement **settles the open question in section 11 for OCR**: it is cheap enough to run eagerly on every image, no opt-in needed. Only the much slower vision-captioning pass stays opt-in.
- **Screenshot location** is not always `~/Desktop`. Read `defaults read com.apple.screencapture location` and fall back to `~/Desktop` (confirmed default on the dev machine).
- **Images with little or no text** (diagrams, photos, charts) get an optional second pass: caption them with `gemma4:12b` vision, which the stack already supports via `analyze_image_bytes()`. This is roughly 2 to 5 seconds per image, so it must be **opt-in per source** and queued behind OCR, never blocking the main index.
- **Scanned PDFs**: when `pypdf` extracts fewer than ~50 characters from a page, rasterize that page and run the same OCR path.
- Store OCR text as normal chunks with `kind="image"` so existing search, citations and MCP tools work unchanged. Citations should reveal the image in Finder and, ideally, show a thumbnail in the chat citations row.

## 5. New capability: ad-hoc file and folder questions

"Any specific files" does not need the index at all, and shipping this early makes the whole release feel immediate.

- Drag a file onto the chat, or attach via a picker, or paste a path.
- The backend reads, extracts (same extractor registry as indexing, including OCR), chunks and, if the content fits the model's context, stuffs it directly into the turn. If it does not fit, embed it into a scratch namespace, retrieve top-k, then discard.
- Zero indexing cost, no permission ceremony beyond the file the user handed over, works on a file that lives anywhere.
- MCP tool: `ask_file(path, question)` so Claude Code gets the same capability.

## 6. Format coverage

Extraction is a registry keyed on extension so new formats are additive:

| Family | Formats | Approach |
|---|---|---|
| Already shipped | md, txt, rst, html, pdf, code | v0.6.0 extractors |
| Office | docx, pptx, xlsx | unzip and strip XML (no heavy dependency) |
| iWork | pages, key, numbers | zip containers, extract the embedded preview PDF |
| Images | png, jpg, heic, webp, tiff | Vision OCR, optional vision caption |
| Apple Notes | notes | read the local SQLite store, read-only |
| Email | eml, mbox | stdlib `email` parser |

Apple Notes and Mail are worth a spike but are the first things to cut if the release gets heavy.

## 7. Permissions and scope UX

macOS TCC gates `~/Desktop`, `~/Documents` and `~/Downloads` behind per-folder consent. Full Disk Access would cover everything in one step but it is a hostile ask for a stranger installing an unsigned app.

- Keep **`NSOpenPanel` with security-scoped bookmarks** as the primary path: the user explicitly grants each root, which is both honest and TCC-friendly. Persist bookmarks so access survives relaunch.
- Add a one-click **"Add my usual folders"** that requests Desktop, Documents, Downloads and the screenshots folder in sequence, each triggering its normal system prompt.
- If a bookmark goes stale or a prompt is denied, the Knowledge page must say exactly which folder lost access and offer a re-grant button. Silent partial indexes are the worst outcome.

## 8. Privacy model

An index of an entire laptop is itself a sensitive artifact, stored as **plaintext chunks** in `~/.omnidev/omnidev.db`. This needs to be deliberate, not implicit.

- **Hard exclusion list**, non-overridable: `~/Library`, `~/.ssh`, keychains, browser profiles, password-manager vaults, `.env`, `.pem`, `id_rsa`, `credentials`, `.aws`, `.git` internals, anything already matched by the existing hidden-file and `EXCLUDED_DIRS` rules.
- **User exclusion list** in Settings, both folders and glob patterns, applied at discovery time.
- Set the database file mode to `0600` and exclude it from Time Machine via `tmutil addexclusion`.
- A visible **"Delete my index"** button that drops all chunks and vectors, plus a per-source delete that already exists.
- README must state plainly what is stored and where. For strangers, this is a trust feature, not a footnote.

## 9. Phasing inside v0.7.0

Ship in this order so each phase is independently demoable:

- **Phase A, foundation**: sqlite-vec store with numpy fallback, no text in RAM, FTS5 plus RRF hybrid retrieval, metadata filters, Spotlight-based discovery replacing `rglob`, FSEvents watcher for incremental updates.
- **Phase B, the headline**: Vision OCR for images and scanned PDFs, screenshot-folder auto-detection, optional vision captions, `kind="image"` citations with thumbnails.
- **Phase C, reach and trust**: ad-hoc file and folder questions plus `ask_file` MCP tool, Office and iWork extractors, "Add my usual folders", exclusion settings, delete-my-index, README privacy section.

Phase C's ad-hoc piece is small enough that it can be pulled forward if the release needs an early win.

## 10. Acceptance

1. First index of Desktop, Documents, Downloads and the screenshots folder on the dev machine completes in **under 20 minutes** and produces a store under **300 MB**, with chat latency unaffected while it runs.
2. A question about text that exists **only inside a screenshot** returns the right answer with that image cited, wifi off.
3. Search stays under **500 ms** at 30k chunks, measured, with resident memory growth under 100 MB.
4. An exact-token query (an error code, an order number) that pure dense retrieval misses is found by the hybrid path. Keep this as a regression test with a fixed corpus.
5. Editing one file updates the index within seconds via FSEvents, with no full rescan.
6. Dragging a file into chat answers a question about it with **no index entry created**.
7. A denied or revoked folder permission produces a specific, actionable message naming the folder.
8. No file from the hard exclusion list appears in the index. Assert this with a test that plants a fake `.env`, `id_rsa` and a Library file.
9. **Indexing a folder containing iCloud-evicted files completes without hanging**, skips them and reports the count. Assert with a unit test that fakes `st_flags` and, before release, a live run against `~/Desktop` on this machine (19 known evicted files).
10. Backend suite green, CI green, release attaches zip and DMG.

## 11. Open decision

**How eager should image captioning be?** OCR is settled: measured at 42 ms warm, it runs eagerly on everything. Vision captioning is the open one, at roughly 2 to 5 seconds per image, so about an hour for 1,200 screenshots. Default is opt-in per source, but if the demo depends on "what was that diagram", eager captioning for the screenshots folder specifically may be worth the one-time cost. Decide after Phase B measures real throughput.

## 12. Out of scope

Signing and notarization (still deferred), Homebrew cask, cloud-drive sources (Google Drive, Dropbox, iCloud, and iCloud is actively hostile on this machine), multi-machine sync, indexing other users' home directories, real-time audio or video transcription.
