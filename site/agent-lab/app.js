const BASELINE_FILES = Object.freeze({
  "calc.py": "def add(a, b):\n    return a - b",
  "test_calc.py": [
    "from calc import add",
    "",
    "def test_adds_positive_operands():",
    "    assert add(2, 3) == 5",
    "",
    "def test_adds_mixed_sign_operands():",
    "    assert add(-4, 9) == 5",
    "",
    "def test_zero_is_identity():",
    "    assert add(0, 0) == 0",
  ].join("\n"),
  "README.md": [
    "# Calculator fixture",
    "",
    "`add(a, b)` returns the arithmetic sum of two numbers.",
    "The implementation must preserve signed values and zero identity.",
  ].join("\n"),
});

const PATCHES = Object.freeze({
  "PATCH-104": {
    id: "PATCH-104",
    target: "PATCH-104 · Correct the operator",
    label: "Correct the operator",
    before: "    return a - b",
    after: "    return a + b",
  },
  "PATCH-127": {
    id: "PATCH-127",
    target: "PATCH-127 · Use the sum primitive",
    label: "Use the sum primitive",
    before: "    return a - b",
    after: "    return sum((a, b))",
  },
  "PATCH-133": {
    id: "PATCH-133",
    target: "PATCH-133 · Return absolute distance",
    label: "Return absolute distance",
    before: "    return a - b",
    after: "    return abs(a - b)",
  },
});

const TESTS = Object.freeze([
  { name: "positive operands", args: [2, 3], expected: 5 },
  { name: "mixed sign operands", args: [-4, 9], expected: 5 },
  { name: "zero identity", args: [0, 0], expected: 0 },
]);

const state = {
  files: { ...BASELINE_FILES },
  selectedFile: "calc.py",
  priorSnapshot: null,
  appliedPatch: null,
  runNumber: 1,
  pendingApproval: null,
  approvedPatch: null,
};

const byId = (id) => document.getElementById(id);
const codeView = byId("code-view");
const codeTitle = byId("code-title");
const restoreButton = byId("restore-button");
const runButton = byId("run-button");
const suiteOutput = byId("suite-output");
const sourceRevision = byId("source-revision");
const sourceState = byId("source-state");
const caseFailing = byId("case-failing");
const auditLog = byId("audit-log");
const receipt = byId("receipt");
const dialog = byId("approval-dialog");
const approvalTitle = byId("approval-title");
const approvalCopy = byId("approval-copy");
const approvalBefore = byId("approval-before");
const approvalAfter = byId("approval-after");
const approveButton = byId("approve-button");
const rejectButton = byId("reject-button");
const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;

function renderCode() {
  const source = state.files[state.selectedFile];
  codeTitle.textContent = state.selectedFile;
  byId("calc-row-content").textContent = state.files["calc.py"].replace(/\s+/g, " ");
  codeView.replaceChildren();

  source.split("\n").forEach((line, index) => {
    const row = document.createElement("span");
    row.className = "code-line";
    if (state.selectedFile === "calc.py" && state.appliedPatch && index === 1) {
      row.classList.add("is-changed");
    }
    row.textContent = line || " ";
    codeView.append(row);
  });

  document.querySelectorAll("[data-open-file]").forEach((button) => {
    const selected = button.dataset.openFile === state.selectedFile;
    if (selected) button.setAttribute("aria-current", "true");
    else button.removeAttribute("aria-current");
    button.closest(".file-row")?.classList.toggle("is-selected", selected);
  });
}

function addAudit(title, detail, tone = "neutral") {
  const item = document.createElement("li");
  const marker = document.createElement("span");
  marker.className = `audit-marker${tone === "good" ? " audit-marker-good" : tone === "bad" ? " audit-marker-bad" : ""}`;
  marker.setAttribute("aria-hidden", "true");

  const copy = document.createElement("div");
  const strong = document.createElement("strong");
  const small = document.createElement("small");
  strong.textContent = title;
  small.textContent = detail;
  copy.append(strong, small);
  item.append(marker, copy);
  auditLog.append(item);

  while (auditLog.children.length > 5) auditLog.firstElementChild?.remove();
}

function setReceipt(kind, title, detail) {
  receipt.className = `receipt${kind ? ` is-${kind}` : ""}`;
  receipt.replaceChildren();
  const label = document.createElement("span");
  const strong = document.createElement("strong");
  const paragraph = document.createElement("p");
  label.className = "receipt-label";
  label.textContent = "latest receipt";
  strong.textContent = title;
  paragraph.textContent = detail;
  receipt.append(label, strong, paragraph);
}

function implementationFor(source) {
  if (source.includes("return a + b")) return (a, b) => a + b;
  if (source.includes("return sum((a, b))")) return (a, b) => a + b;
  if (source.includes("return abs(a - b)")) return (a, b) => Math.abs(a - b);
  if (source.includes("return a - b")) return (a, b) => a - b;
  return null;
}

function currentResults() {
  const implementation = implementationFor(state.files["calc.py"]);
  return TESTS.map((test) => {
    const actual = implementation ? implementation(...test.args) : "unsupported";
    return { ...test, actual, passed: actual === test.expected };
  });
}

function renderResult(row, result, status = result.passed ? "pass" : "fail") {
  row.querySelector("[data-test-actual]").textContent = String(result.actual);
  const stateNode = row.querySelector("[data-test-state]");
  stateNode.textContent = status;
  stateNode.className = `test-state is-${status}`;
}

async function runTests({ quiet = false } = {}) {
  const rows = [...document.querySelectorAll("[data-test-case]")];
  const results = currentResults();
  runButton.disabled = true;
  suiteOutput.className = "suite-output is-running";
  suiteOutput.textContent = "running 0 / 3";

  rows.forEach((row, index) => renderResult(row, results[index], "waiting"));

  for (let index = 0; index < rows.length; index += 1) {
    renderResult(rows[index], results[index], "running");
    if (!reduceMotion) await new Promise((resolve) => window.setTimeout(resolve, 180));
    renderResult(rows[index], results[index]);
    suiteOutput.textContent = `running ${index + 1} / 3`;
  }

  const passed = results.filter((result) => result.passed).length;
  const failed = results.length - passed;
  suiteOutput.textContent = `${passed} pass · ${failed} fail`;
  suiteOutput.className = `suite-output${failed === 0 ? " is-passing" : ""}`;
  caseFailing.textContent = `${failed} of ${results.length}`;
  sourceState.textContent = failed === 0 ? "tests passing" : "tests failing";
  sourceState.className = `source-state ${failed === 0 ? "source-state-good" : "source-state-bad"}`;
  runButton.disabled = false;

  if (!quiet) addAudit("Checks completed", `${passed} passed, ${failed} failed`, failed === 0 ? "good" : "bad");
  return { passed, failed, total: results.length, results };
}

function patchFromRequest({ patchId, target } = {}) {
  if (patchId && PATCHES[patchId]) return PATCHES[patchId];
  return Object.values(PATCHES).find((patch) => patch.target === target) ?? null;
}

function setPatchControlsDisabled(disabled) {
  document.querySelectorAll("[data-apply-patch]").forEach((button) => {
    button.disabled = disabled;
  });
}

async function commitPatch(patch) {
  const source = state.files["calc.py"];
  const matches = source.split(patch.before).length - 1;
  if (matches !== 1) {
    throw new Error("The exact baseline replacement no longer matches. Restore the snapshot before applying another patch.");
  }

  state.priorSnapshot = { ...state.files };
  state.files["calc.py"] = source.replace(patch.before, patch.after);
  state.appliedPatch = patch.id;
  state.runNumber += 1;
  state.selectedFile = "calc.py";
  renderCode();
  restoreButton.disabled = false;
  setPatchControlsDisabled(true);
  sourceRevision.textContent = `fixture r${state.runNumber}`;
  document.querySelectorAll("[data-patch-id]").forEach((row) => {
    row.classList.toggle("is-active", row.dataset.patchId === patch.id);
  });

  const tests = await runTests({ quiet: true });
  addAudit("Approved change applied", `${patch.id} changed one line`, "good");
  addAudit("Verification finished", `${tests.passed} passed, ${tests.failed} failed`, tests.failed === 0 ? "good" : "bad");
  setReceipt(
    "success",
    `${patch.id} applied locally`,
    `One exact replacement, ${tests.passed} of ${tests.total} checks passing. Snapshot r${state.runNumber - 1} can be restored.`,
  );
  return tests;
}

function closePendingApproval(result) {
  const pending = state.pendingApproval;
  if (!pending) return;
  state.pendingApproval = null;
  pending.signal?.removeEventListener("abort", pending.abortHandler);
  if (dialog.open) dialog.close();
  pending.resolve(result);
}

function rejectPendingApproval(reason = "The in-page patch request was rejected.") {
  const patch = state.pendingApproval?.patch;
  if (patch) addAudit("Decision rejected", `${patch.id} left the fixture unchanged`, "bad");
  document.querySelectorAll("[data-patch-id]").forEach((row) => row.classList.remove("is-active"));
  setReceipt("rejected", "Change rejected", reason);
  closePendingApproval(false);
}

export function requestPatchConfirmation({ patchId, target, source = "agent", signal } = {}) {
  const patch = patchFromRequest({ patchId, target });
  if (!patch) return Promise.reject(new Error("Choose one exact patch candidate returned by list_patches."));
  if (state.pendingApproval) return Promise.reject(new Error("Another patch request is already waiting for an in-page decision."));
  if (state.approvedPatch) return Promise.reject(new Error("An approved patch is still waiting to be applied."));
  if (state.appliedPatch) return Promise.reject(new Error("Restore the previous snapshot before applying another patch."));
  if (signal?.aborted) return Promise.reject(signal.reason ?? new Error("Patch request aborted."));

  state.selectedFile = "calc.py";
  renderCode();
  document.querySelectorAll("[data-patch-id]").forEach((row) => {
    row.classList.toggle("is-active", row.dataset.patchId === patch.id);
  });
  approvalTitle.textContent = source === "agent"
    ? "An agent is requesting a local change."
    : "Review this local change.";
  approvalCopy.textContent = `${patch.id} proposes one exact replacement in calc.py. Nothing changes until you choose Approve patch.`;
  approvalBefore.textContent = `- ${patch.before.trim()}`;
  approvalAfter.textContent = `+ ${patch.after.trim()}`;
  approveButton.disabled = false;
  rejectButton.disabled = false;
  approveButton.textContent = "Approve patch";

  if (typeof dialog.showModal === "function") dialog.showModal();
  else dialog.setAttribute("open", "");
  addAudit("Approval requested", `${patch.id} is waiting for an in-page decision`, "neutral");
  setReceipt("", "Decision pending", `${patch.id} has not changed any state.`);

  return new Promise((resolve, reject) => {
    const abortHandler = () => {
      if (dialog.open) dialog.close();
      state.pendingApproval = null;
      document.querySelectorAll("[data-patch-id]").forEach((row) => row.classList.remove("is-active"));
      addAudit("Request cancelled", `${patch.id} was cancelled before approval`, "neutral");
      setReceipt("rejected", "Request cancelled", "No fixture state changed.");
      reject(signal.reason ?? new Error("Patch request aborted."));
    };
    state.pendingApproval = { patch, resolve, reject, signal, abortHandler };
    signal?.addEventListener("abort", abortHandler, { once: true });
  });
}

export async function applyApprovedPatch({ patchId, target, signal } = {}) {
  const patch = patchFromRequest({ patchId, target });
  if (!patch) throw new Error("Choose one exact patch candidate returned by list_patches.");
  const approval = state.approvedPatch;
  if (signal?.aborted) {
    approval?.signal?.removeEventListener("abort", approval.abortHandler);
    state.approvedPatch = null;
    throw signal.reason ?? new Error("Patch request aborted before the approved change was applied.");
  }
  if (approval?.patchId !== patch.id) {
    throw new Error("Blocked: this exact patch does not have a fresh in-page approval.");
  }

  approval.signal?.removeEventListener("abort", approval.abortHandler);
  state.approvedPatch = null;
  const tests = await commitPatch(patch);
  return {
    approved: true,
    patchId: patch.id,
    replacement: { before: patch.before.trim(), after: patch.after.trim() },
    tests: { passed: tests.passed, failed: tests.failed, total: tests.total },
    restoreAvailable: true,
  };
}

export async function requestPatchApproval(options = {}) {
  const approved = await requestPatchConfirmation(options);
  if (!approved) {
    return { approved: false, reason: "The in-page patch request was rejected." };
  }
  return applyApprovedPatch(options);
}

approveButton.addEventListener("click", (event) => {
  const pending = state.pendingApproval;
  if (!pending) return;
  if (!event.isTrusted) {
    approvalCopy.textContent = "Approval requires a trusted user gesture. The fixture is still unchanged.";
    return;
  }
  if (pending.signal?.aborted) {
    pending.abortHandler();
    return;
  }

  // A trusted browser input event mints this demo's single-use in-page approval.
  // This is deliberately not presented as authenticated out-of-band authorization.
  pending.signal?.removeEventListener("abort", pending.abortHandler);
  approveButton.disabled = true;
  rejectButton.disabled = true;
  approveButton.textContent = "Approved";
  const approvedAbortHandler = () => {
    if (state.approvedPatch?.patchId !== pending.patch.id) return;
    state.approvedPatch = null;
    document.querySelectorAll("[data-patch-id]").forEach((row) => row.classList.remove("is-active"));
    addAudit("Approval revoked", `${pending.patch.id} was cancelled before application`, "neutral");
    setReceipt("rejected", "Approval revoked", "No fixture state changed.");
  };
  state.approvedPatch = {
    patchId: pending.patch.id,
    signal: pending.signal,
    abortHandler: approvedAbortHandler,
  };
  pending.signal?.addEventListener("abort", approvedAbortHandler, { once: true });
  addAudit("Approved in page", `${pending.patch.id} authorized once`, "good");
  setReceipt("", "Approval granted", `${pending.patch.id} is authorized for this request only.`);
  closePendingApproval(true);
});

rejectButton.addEventListener("click", () => rejectPendingApproval());

dialog.addEventListener("cancel", (event) => {
  event.preventDefault();
  rejectPendingApproval("The in-page patch request was rejected with Escape.");
});

document.querySelectorAll("[data-open-file]").forEach((button) => {
  button.addEventListener("click", (event) => {
    event.preventDefault();
    state.selectedFile = button.dataset.openFile;
    renderCode();
  });
});

document.querySelectorAll("[data-apply-patch]").forEach((button) => {
  button.addEventListener("click", () => {
    requestPatchApproval({ patchId: button.dataset.applyPatch, source: "human-ui" }).catch((error) => {
      setReceipt("rejected", "Request could not open", error instanceof Error ? error.message : String(error));
    });
  });
});

restoreButton.addEventListener("click", async () => {
  if (!state.priorSnapshot) return;
  state.approvedPatch?.signal?.removeEventListener("abort", state.approvedPatch.abortHandler);
  state.files = { ...state.priorSnapshot };
  state.priorSnapshot = null;
  state.appliedPatch = null;
  state.approvedPatch = null;
  state.runNumber += 1;
  state.selectedFile = "calc.py";
  renderCode();
  restoreButton.disabled = true;
  setPatchControlsDisabled(false);
  sourceRevision.textContent = `fixture r${state.runNumber}`;
  document.querySelectorAll("[data-patch-id]").forEach((row) => row.classList.remove("is-active"));
  const tests = await runTests({ quiet: true });
  addAudit("Snapshot restored", `Baseline returned with ${tests.failed} failing checks`, "neutral");
  setReceipt("", "Previous version restored", "The applied replacement was reversed from the in-memory snapshot.");
});

runButton.addEventListener("click", () => { void runTests(); });

renderCode();
