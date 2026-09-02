import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const labRoot = resolve(root, "site/agent-lab");
const paths = {
  html: resolve(labRoot, "index.html"),
  styles: resolve(labRoot, "styles.css"),
  adapter: resolve(labRoot, "graft-adapter.js"),
  adapterDigest: resolve(labRoot, "graft-adapter.js.sha256"),
  review: resolve(labRoot, "graft-review.json"),
  ownerHandlers: resolve(labRoot, "owner-handlers.js"),
  app: resolve(labRoot, "app.js"),
  vercel: resolve(root, "vercel.json"),
};

const [html, styles, adapter, adapterDigestSource, reviewSource, ownerHandlers, app, vercelSource] = await Promise.all([
  readFile(paths.html, "utf8"),
  readFile(paths.styles, "utf8"),
  readFile(paths.adapter, "utf8"),
  readFile(paths.adapterDigest, "utf8"),
  readFile(paths.review, "utf8"),
  readFile(paths.ownerHandlers, "utf8"),
  readFile(paths.app, "utf8"),
  readFile(paths.vercel, "utf8"),
]);

const sha256 = (value) => createHash("sha256").update(value).digest("hex");
const isSha256 = (value) => typeof value === "string" && /^[0-9a-f]{64}$/.test(value);
const EXPECTED_GRAFT_REVISION = "670110f353e7c859f6c506d834d83e3e6118e227";
const EXPECTED_GENERATOR_SOURCES_SHA256 =
  "51ab7414139f376bb7bcbb39ce13d77c91d71ee4bef13e76d809e747f8af3193";

function exportedJson(name) {
  const prefix = `export const ${name} = `;
  const start = adapter.indexOf(prefix);
  assert(start >= 0, `Missing ${name} export.`);
  let valueStart = start + prefix.length;
  while (/\s/.test(adapter[valueStart])) valueStart += 1;
  assert(
    adapter[valueStart] === "{" || adapter[valueStart] === "[",
    `${name} is not a JSON object or array.`,
  );

  const stack = [];
  let inString = false;
  let escaped = false;
  for (let index = valueStart; index < adapter.length; index += 1) {
    const character = adapter[index];
    if (inString) {
      if (escaped) escaped = false;
      else if (character === "\\") escaped = true;
      else if (character === '"') inString = false;
      continue;
    }
    if (character === '"') {
      inString = true;
      continue;
    }
    if (character === "{") stack.push("}");
    else if (character === "[") stack.push("]");
    else if (character === "}" || character === "]") {
      assert.equal(character, stack.pop(), `Unbalanced JSON while reading ${name}.`);
      if (stack.length === 0) return JSON.parse(adapter.slice(valueStart, index + 1));
    }
  }
  throw new Error(`Could not delimit ${name}.`);
}

function extractRuntime() {
  const prefix =
    "/* ---- Graft runtime, inlined. No network calls, no dependency on Graft. ---- */\n";
  const suffix = "\n/* ---- end runtime ---- */";
  const start = adapter.indexOf(prefix);
  const end = adapter.indexOf(suffix, start + prefix.length);
  assert(start >= 0 && end > start, "Could not delimit the inlined Graft runtime.");
  return adapter.slice(start + prefix.length, end);
}

const manifest = exportedJson("graftManifest");
const tools = exportedJson("graftTools");
const review = JSON.parse(reviewSource);
const inlinedRuntime = extractRuntime();

const expectedNames = [
  "get_page_summary",
  "get_page_outline",
  "list_files",
  "get_file",
  "list_patches",
  "get_patch",
  "list_test_results",
  "apply_patch",
];
const expectedFiles = ["calc.py", "test_calc.py", "README.md"];
const expectedPatches = ["PATCH-104", "PATCH-127", "PATCH-133"];
const expectedTargets = [
  "PATCH-104 · Correct the operator",
  "PATCH-127 · Use the sum primitive",
  "PATCH-133 · Return absolute distance",
];
const expectedReview = {
  version: 1,
  decisions: [{ name: "apply_patch", status: "published" }],
};

assert.equal(manifest.product, "Graft", "Adapter manifest is not a Graft export.");
assert.equal(manifest.version, 1, "Unsupported Graft manifest version.");
assert.equal(
  manifest.source?.url,
  "https://omnidev-flame.vercel.app/agent-lab/",
  "Agent Review Room owner URL drifted.",
);
assert.equal(manifest.source?.kind, "owner-html", "The adapter was not built from owner HTML.");
assert.equal(manifest.source?.file, "index.html", "The manifest source file drifted.");
assert(Number.isFinite(Date.parse(manifest.generatedAt)), "generatedAt is not a valid timestamp.");

assert(
  manifest.provenance?.graftRevision === EXPECTED_GRAFT_REVISION,
  "graftRevision does not match the pinned reviewed Graft commit.",
);
assert(
  manifest.provenance?.graftSourceState === "clean",
  "The Agent Review Room adapter was generated from a dirty Graft working tree.",
);
assert(
  manifest.provenance?.generatorSourcesSha256 === EXPECTED_GENERATOR_SOURCES_SHA256,
  "generatorSourcesSha256 does not match the pinned reviewed Graft source.",
);
assert.equal(
  manifest.provenance?.sourceHtmlSha256,
  sha256(html),
  "Agent Review Room HTML changed without regenerating its adapter.",
);
assert.equal(
  manifest.provenance?.runtimeSha256,
  sha256(inlinedRuntime),
  "Inlined runtime bytes do not match their provenance hash.",
);
assert.equal(
  manifest.provenance?.exportedToolsSha256,
  sha256(JSON.stringify(tools)),
  "Exported tool payload does not match its provenance hash.",
);
assert(
  /^g_[a-z0-9]+$/.test(manifest.provenance?.sanitizedSnapshotFingerprint ?? ""),
  "Sanitized snapshot fingerprint is missing or malformed.",
);
assert(
  /^g_[a-z0-9]+$/.test(manifest.provenance?.reviewedToolSetFingerprint ?? ""),
  "Reviewed tool-set fingerprint is missing or malformed.",
);

assert.deepEqual(review, expectedReview, "The human review file contains an unexpected decision.");
assert.deepEqual(
  manifest.provenance?.humanReview,
  {
    version: review.version,
    file: "graft-review.json",
    sha256: sha256(reviewSource),
    decisions: review.decisions,
  },
  "The manifest does not reproduce the exact human review artifact.",
);

const declaredAdapterDigest = adapterDigestSource.trim().split(/\s+/)[0];
assert(isSha256(declaredAdapterDigest), "Adapter sidecar does not start with a SHA-256 digest.");
assert.equal(declaredAdapterDigest, sha256(adapter), "Adapter bytes do not match the detached digest.");

assert.deepEqual(
  tools.map((tool) => tool.name),
  expectedNames,
  "The exported Agent Review Room tool set drifted.",
);
assert.deepEqual(
  manifest.tools.map((tool) => tool.name),
  expectedNames,
  "The manifest tool set drifted.",
);
assert.equal(new Set(expectedNames).size, tools.length, "Tool names are not unique.");

for (let index = 0; index < tools.length; index += 1) {
  const tool = tools[index];
  const manifestTool = manifest.tools[index];
  const { status, ...manifestDescriptor } = manifestTool;
  assert.deepEqual(manifestDescriptor, tool, `${tool.name} differs between manifest and export.`);
  assert(/^[a-z][a-z0-9_]{0,29}$/.test(tool.name), `${tool.name} is not a valid tool name.`);
  assert.equal(tool.inputSchema?.type, "object", `${tool.name} must accept an object schema.`);
  assert.equal(
    tool.inputSchema?.additionalProperties,
    false,
    `${tool.name} must reject undeclared arguments.`,
  );
  assert.equal(
    tool.annotations?.untrustedContentHint,
    true,
    `${tool.name} must identify page-derived content as untrusted.`,
  );
  assert.equal(
    tool.annotations?.readOnlyHint,
    tool.readOnly,
    `${tool.name} read-only annotation drifted from its reviewed contract.`,
  );
  assert.equal(
    status,
    tool.name === "apply_patch" ? "published" : "auto",
    `${tool.name} has an unexpected review status.`,
  );
}

const byName = Object.fromEntries(tools.map((tool) => [tool.name, tool]));
assert.equal(byName.get_page_summary.binding?.kind, "summary");
assert.equal(byName.get_page_outline.binding?.kind, "outline");

assert.equal(byName.list_files.binding?.kind, "collection");
assert.equal(byName.list_files.selector, "#file-list");
assert.equal(byName.get_file.binding?.kind, "collection_item");
assert.equal(byName.get_file.binding?.keyField, "file_id");
assert.deepEqual(byName.get_file.inputSchema?.required, ["file_id"]);
assert.deepEqual(byName.get_file.inputSchema?.properties?.file_id?.enum, expectedFiles);

assert.equal(byName.list_patches.binding?.kind, "collection");
assert.equal(byName.list_patches.selector, "#patch-list");
assert.equal(byName.get_patch.binding?.kind, "collection_item");
assert.equal(byName.get_patch.binding?.keyField, "patch_id");
assert.deepEqual(byName.get_patch.inputSchema?.required, ["patch_id"]);
assert.deepEqual(byName.get_patch.inputSchema?.properties?.patch_id?.enum, expectedPatches);

assert.equal(byName.list_test_results.binding?.kind, "table");
assert.equal(byName.list_test_results.selector, "#test-results");
assert.deepEqual(
  byName.list_test_results.binding?.columns?.map(({ key, label, index }) => ({ key, label, index })),
  [
    { key: "case", label: "Case", index: 0 },
    { key: "assertion", label: "Assertion", index: 1 },
    { key: "actual", label: "Actual", index: 2 },
    { key: "result", label: "Result", index: 3 },
  ],
  "Test result columns drifted from the visible deterministic runner.",
);
assert(
  !("duration" in (byName.list_test_results.inputSchema?.properties ?? {})),
  "The removed fabricated duration field returned to the contract.",
);

const applyPatch = byName.apply_patch;
assert.equal(applyPatch.binding?.kind, "action_candidate");
assert.equal(applyPatch.action, "unbound_write");
assert.equal(applyPatch.readOnly, false);
assert.equal(applyPatch.destructive, true);
assert.deepEqual(applyPatch.inputSchema?.required, ["target"]);
assert.deepEqual(applyPatch.inputSchema?.properties?.target?.enum, expectedTargets);
assert.deepEqual(applyPatch.binding?.targets, expectedTargets);
assert(
  !/no handler is bound|site Graft does not own/i.test(applyPatch.description),
  "apply_patch still has the obsolete unbound-handler explanation.",
);
assert(
  tools.filter((tool) => tool.destructive).length === 1,
  "Only the human-held apply_patch tool may be destructive.",
);

const scriptSources = [...html.matchAll(/<script\b[^>]*\bsrc=["']([^"']+)["'][^>]*>/gi)].map(
  (match) => match[1],
);
assert.deepEqual(
  scriptSources,
  ["./owner-handlers.js"],
  "The page must load only the thin owner bootstrap.",
);
assert(html.includes('id="webmcp-state"'), "The live WebMCP state marker is missing.");
assert(
  !styles.includes(".topbar-state span:last-child"),
  "Responsive CSS hides the live WebMCP state marker.",
);
assert(
  /<dialog\b[^>]*id="approval-dialog"[^>]*data-graft-ignore[^>]*>/i.test(html),
  "The approval boundary must be excluded from compiler extraction.",
);
assert.equal((html.match(/data-file-id=/g) ?? []).length, 3, "Expected exactly three fixture files.");
assert.equal((html.match(/data-patch-id=/g) ?? []).length, 3, "Expected exactly three patch rows.");
assert.equal(
  (html.match(/data-field="review_score"/g) ?? []).length,
  3,
  "Every patch must expose an explicit fixture review score.",
);
assert(!/data-field=["']confidence["']/i.test(html), "A model-confidence field returned to the UI.");
assert(!/<th\b[^>]*>\s*Duration\s*<\/th>/i.test(html), "A fabricated duration column returned.");
assert(
  html.includes('data-field="content_continued"') &&
    html.includes("def test_zero_is_identity():") &&
    html.includes("The implementation must preserve signed values and zero identity."),
  "The generated file tools no longer expose the complete fixture evidence.",
);
assert.equal(
  (html.match(/aria-describedby="patch-(?:104|127|133)-title"/g) ?? []).length,
  3,
  "Patch controls must identify the proposal they apply.",
);

assert(
  /import\s*{\s*registerGraftTools\s*}\s*from\s*["']\.\/graft-adapter\.js["']/.test(
    ownerHandlers,
  ),
  "Owner bootstrap does not import the generated adapter.",
);
assert(
  /import\s*{\s*applyApprovedPatch\s*,\s*requestPatchConfirmation\s*}\s*from\s*["']\.\/app\.js["']/.test(
    ownerHandlers,
  ),
  "Owner bootstrap does not import the two-stage approval boundary.",
);
assert(ownerHandlers.includes("registerGraftTools({"), "Owner bootstrap does not register Graft tools.");
assert(
  /confirm\s*:\s*\(\{\s*args\s*,\s*signal\s*}\)\s*=>\s*requestPatchConfirmation\s*\(\{/.test(
    ownerHandlers,
  ),
  "The generated destructive gate is not bound to visible human confirmation.",
);
assert(/handlers\s*:\s*{[\s\S]*apply_patch\s*:/.test(ownerHandlers), "apply_patch lacks its owner handler.");
assert(
  ownerHandlers.includes("requestPatchConfirmation({") && ownerHandlers.includes('source: "agent"'),
  "The adapter confirmation gate does not route into the visible agent approval flow.",
);
assert(
  ownerHandlers.includes("applyApprovedPatch({"),
  "The owner handler does not consume the single-use human approval.",
);
assert(
  ownerHandlers.includes("signal: context.signal"),
  "The owner action does not propagate agent cancellation.",
);
assert(
  ownerHandlers.includes("Object.keys(args).length === 1") &&
    ownerHandlers.includes('typeof args.target === "string"'),
  "The owner action lost its defense-in-depth exact-input check.",
);
assert(!/\.registerTool\s*\(/.test(ownerHandlers), "Owner code declares a WebMCP tool directly.");
assert(!/document\.modelContext|navigator\.modelContext/.test(ownerHandlers), "Owner code bypasses Graft registration.");

assert(
  app.includes("export function requestPatchConfirmation"),
  "The human confirmation API is not exported.",
);
assert(app.includes("export async function applyApprovedPatch"), "The approved mutation API is not exported.");
const trustedGesture = app.indexOf("if (!event.isTrusted)");
const detachPendingAbort = app.indexOf('removeEventListener("abort", pending.abortHandler)', trustedGesture);
const mintApproval = app.indexOf("state.approvedPatch = {", detachPendingAbort);
const installApprovedAbort = app.indexOf(
  'pending.signal?.addEventListener("abort", approvedAbortHandler',
  mintApproval,
);
const resolveConfirmation = app.indexOf("closePendingApproval(true)", installApprovedAbort);
assert(trustedGesture >= 0, "Approval no longer requires a trusted user gesture.");
assert(
  detachPendingAbort > trustedGesture &&
    mintApproval > detachPendingAbort &&
    installApprovedAbort > mintApproval &&
    resolveConfirmation > installApprovedAbort,
  "Approval must transfer abort handling to the single-use token before confirmation resolves.",
);
assert(
  /const approvedAbortHandler = \(\) => \{[\s\S]*state\.approvedPatch = null;[\s\S]*classList\.remove\("is-active"\)/.test(
    app,
  ),
  "An abort after approval must revoke the unused token and clear its visible selection.",
);
const approvalGuard = app.indexOf("approval?.patchId !== patch.id");
const detachApprovedAbort = app.indexOf(
  'approval.signal?.removeEventListener("abort", approval.abortHandler)',
  approvalGuard,
);
const consumeApproval = app.indexOf("state.approvedPatch = null", approvalGuard);
const commit = app.indexOf("await commitPatch(patch)", approvalGuard);
assert(
  approvalGuard >= 0 &&
    detachApprovedAbort > approvalGuard &&
    consumeApproval > detachApprovedAbort &&
    commit > consumeApproval,
  "The mutation must validate the exact token, detach cancellation and consume it before committing.",
);
assert(app.includes("if (matches !== 1)"), "Patch application lost its one-occurrence guard.");
assert(app.includes("source.replace(patch.before, patch.after)"), "Patch application is no longer bounded.");
assert(app.includes("if (state.pendingApproval)"), "Concurrent approval requests are not rejected.");
assert(!/window\.__|globalThis\.__/.test(app), "A fixture debug global is exposed.");

const vercel = JSON.parse(vercelSource);
const agentLabHeaders = vercel.headers?.find(({ source }) => source === "/agent-lab/(.*)")?.headers ?? [];
const headerMap = Object.fromEntries(agentLabHeaders.map(({ key, value }) => [key.toLowerCase(), value]));
assert.equal(
  headerMap["content-security-policy"],
  "frame-ancestors 'none'",
  "Agent Review Room must deny framing through CSP.",
);
assert.equal(headerMap["x-frame-options"], "DENY", "Agent Review Room must deny legacy framing.");

for (const [name, source] of [
  ["graft-adapter.js", adapter],
  ["owner-handlers.js", ownerHandlers],
  ["app.js", app],
]) {
  assert(
    !/\b(?:fetch|eval)\s*\(|\b(?:XMLHttpRequest|WebSocket|EventSource|indexedDB|localStorage|sessionStorage)\b|new\s+Function\b/.test(
      source,
    ),
    `${name} introduced network, dynamic-code or persistence access.`,
  );
}

const registeredDescriptors = [];
const unregisteredNames = [];
const originalDocument = globalThis.document;
globalThis.document = {
  modelContext: {
    registerTool: async (descriptor) => registeredDescriptors.push(descriptor),
    unregisterTool: async (name) => unregisteredNames.push(name),
  },
};

let ownerCalls = 0;
let allowConfirmation = false;
const confirmationRequests = [];

try {
  const adapterModule = await import(
    `data:text/javascript;base64,${Buffer.from(adapter).toString("base64")}`
  );
  const report = await adapterModule.registerGraftTools({
    handlers: {
      apply_patch: async (args) => {
        ownerCalls += 1;
        return { ok: true, applied: args.target };
      },
    },
    confirm: async (request) => {
      confirmationRequests.push(request);
      return allowConfirmation;
    },
  });

  assert.deepEqual(report.failures, [], "Generated registration reported a failure.");
  assert.deepEqual(report.missingHandlers, [], "Generated registration is missing a runtime handler.");
  assert.deepEqual(report.registered, expectedNames, "Generated registration returned the wrong names.");
  assert.deepEqual(
    registeredDescriptors.map((descriptor) => descriptor.name),
    expectedNames,
    "Native WebMCP descriptors do not match the reviewed tool set.",
  );
  assert(
    registeredDescriptors.every((descriptor) => typeof descriptor.execute === "function"),
    "A registered descriptor has no executable handler.",
  );

  const nativeApplyPatch = registeredDescriptors.find(({ name }) => name === "apply_patch");
  assert(nativeApplyPatch, "apply_patch was not registered natively.");

  for (const poisonKey of ["constructor", "toString", "__proto__"]) {
    const args = JSON.parse(`{"target":${JSON.stringify(expectedTargets[0])},"${poisonKey}":"smuggled"}`);
    const callsBefore = ownerCalls;
    const confirmationsBefore = confirmationRequests.length;
    let rejected = false;
    try {
      const result = await nativeApplyPatch.execute(args);
      rejected = result?.isError === true || result?.ok === false;
    } catch {
      rejected = true;
    }
    assert(rejected, `Undeclared prototype key ${poisonKey} was accepted.`);
    assert.equal(ownerCalls, callsBefore, `${poisonKey} reached the owner handler.`);
    assert.equal(
      confirmationRequests.length,
      confirmationsBefore,
      `${poisonKey} reached confirmation before schema rejection.`,
    );
  }

  const callsBeforeRejection = ownerCalls;
  const confirmationsBeforeRejection = confirmationRequests.length;
  let rejectedResult;
  let rejectedByThrow = false;
  try {
    rejectedResult = await nativeApplyPatch.execute({ target: expectedTargets[0] });
  } catch {
    rejectedByThrow = true;
  }
  assert.equal(ownerCalls, callsBeforeRejection, "Rejected confirmation reached the owner handler.");
  assert.equal(
    confirmationRequests.length,
    confirmationsBeforeRejection + 1,
    "Destructive override did not request confirmation.",
  );
  assert(
    rejectedByThrow || rejectedResult?.isError === true || rejectedResult?.ok === false,
    "Rejected confirmation did not return a blocked result.",
  );

  allowConfirmation = true;
  const approvedResult = await nativeApplyPatch.execute({ target: expectedTargets[0] });
  assert.equal(ownerCalls, callsBeforeRejection + 1, "Approved action did not reach the owner handler once.");
  assert.equal(approvedResult?.ok, true, "Approved owner result did not return to the caller.");
  assert.equal(confirmationRequests.at(-1)?.tool?.name, "apply_patch");
  assert.deepEqual(confirmationRequests.at(-1)?.args, { target: expectedTargets[0] });

  await report.cleanup();
  assert.deepEqual(unregisteredNames.sort(), [...expectedNames].sort(), "Generated cleanup is incomplete.");
} finally {
  if (originalDocument === undefined) delete globalThis.document;
  else globalThis.document = originalDocument;
}

console.log(
  "Agent Review Room provenance, contract, bootstrap and destructive-boundary checks passed.",
);
