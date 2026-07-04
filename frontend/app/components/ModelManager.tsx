"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Check, Cpu, Download, Loader2, RefreshCw } from "lucide-react";
import { API_BASE } from "@/lib/api";

type InstalledModel = {
  name: string;
  size_gb: number | null;
  parameter_size: string;
  quantization: string;
};

type RecommendedModel = {
  name: string;
  label: string;
  size_gb: number;
  roles: string[];
  note: string;
  recommended: boolean;
};

type ProviderStatus = {
  provider: string;
  text_model: string;
  vision_model: string;
  reachable: boolean;
  installed: string[];
  text_model_ready: boolean;
  vision_model_ready: boolean;
};

type ModelsResponse = {
  status: ProviderStatus;
  installed: InstalledModel[];
  recommended: RecommendedModel[];
};

type PullState = {
  name: string;
  status: string;
  percent: number | null;
  error?: string;
};

export default function ModelManager() {
  const [data, setData] = useState<ModelsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [pull, setPull] = useState<PullState | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/models`, { cache: "no-store" });
      if (res.ok) setData(await res.json());
    } catch {
      /* backend offline — leave last known state */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    return () => abortRef.current?.abort();
  }, [load]);

  const pullModel = useCallback(
    async (name: string) => {
      abortRef.current?.abort();
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      setPull({ name, status: "starting", percent: null });

      try {
        const res = await fetch(`${API_BASE}/api/models/pull`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name }),
          signal: ctrl.signal,
        });
        if (!res.ok || !res.body) {
          setPull({ name, status: "failed", percent: null, error: `HTTP ${res.status}` });
          return;
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        for (;;) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";
          for (const line of lines) {
            if (!line.trim()) continue;
            let ev: Record<string, unknown>;
            try {
              ev = JSON.parse(line);
            } catch {
              continue;
            }
            if (ev.error) {
              setPull({ name, status: "failed", percent: null, error: String(ev.error) });
              return;
            }
            const completed = typeof ev.completed === "number" ? ev.completed : null;
            const total = typeof ev.total === "number" ? ev.total : null;
            const percent =
              completed !== null && total ? Math.round((completed / total) * 100) : null;
            setPull({ name, status: String(ev.status ?? "downloading"), percent });
            if (ev.status === "success") {
              setPull({ name, status: "success", percent: 100 });
            }
          }
        }
        await load();
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setPull({ name, status: "failed", percent: null, error: String(err) });
        }
      }
    },
    [load],
  );

  if (loading || !data) return null;
  const { status, recommended } = data;

  // Only relevant for the local Ollama provider.
  if (status.provider !== "ollama") return null;

  const defaultReady = status.text_model_ready && status.vision_model_ready;
  const installedSet = new Set(status.installed.map((n) => n.split(":")[0] + ":" + (n.split(":")[1] ?? "")));

  return (
    <section className="modelManager" aria-label="Local models">
      <div className="modelManagerHead">
        <h2>
          <Cpu size={16} aria-hidden="true" /> Local models
        </h2>
        <button type="button" onClick={load} className="modelRefresh" title="Refresh">
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      {!status.reachable && (
        <p className="modelHint modelHintWarn">
          Ollama isn&apos;t reachable. Install it from{" "}
          <a href="https://ollama.com" target="_blank" rel="noreferrer">
            ollama.com
          </a>{" "}
          and run <code>ollama serve</code>, then refresh.
        </p>
      )}

      {status.reachable && !defaultReady && (
        <p className="modelHint modelHintWarn">
          Your default model <code>{status.text_model}</code> isn&apos;t installed yet. Pull it to
          run OmniDev fully offline.
        </p>
      )}
      {status.reachable && defaultReady && (
        <p className="modelHint modelHintOk">
          <Check size={13} /> <code>{status.text_model}</code> is ready. OmniDev runs fully offline.
        </p>
      )}

      {pull && (
        <div className={`modelPull ${pull.status === "failed" ? "failed" : ""}`}>
          <div className="modelPullTop">
            <span>
              {pull.status === "success" ? (
                <Check size={13} />
              ) : pull.status === "failed" ? null : (
                <Loader2 size={13} className="spin" />
              )}
              {pull.name} — {pull.error ? pull.error : pull.status}
            </span>
            {pull.percent !== null && <span>{pull.percent}%</span>}
          </div>
          {pull.percent !== null && pull.status !== "failed" && (
            <div className="modelPullTrack">
              <div className="modelPullFill" style={{ width: `${pull.percent}%` }} />
            </div>
          )}
        </div>
      )}

      {status.reachable && (
        <ul className="modelList">
          {recommended.map((m) => {
            const key = m.name.split(":")[0] + ":" + (m.name.split(":")[1] ?? "");
            const isInstalled = installedSet.has(key);
            const isPulling = pull?.name === m.name && pull.status !== "success" && pull.status !== "failed";
            return (
              <li key={m.name} className="modelRow">
                <div className="modelRowInfo">
                  <div className="modelRowTitle">
                    {m.label}
                    <code>{m.name}</code>
                    {m.recommended && <span className="modelTag">default</span>}
                  </div>
                  <p>{m.note}</p>
                  <div className="modelRoles">
                    <span>{m.size_gb} GB</span>
                    {m.roles.map((r) => (
                      <span key={r}>{r}</span>
                    ))}
                  </div>
                </div>
                {isInstalled ? (
                  <span className="modelInstalled">
                    <Check size={13} /> Installed
                  </span>
                ) : (
                  <button
                    type="button"
                    className="modelPullBtn"
                    disabled={isPulling}
                    onClick={() => pullModel(m.name)}
                  >
                    {isPulling ? <Loader2 size={13} className="spin" /> : <Download size={13} />}
                    {isPulling ? "Pulling…" : "Pull"}
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
