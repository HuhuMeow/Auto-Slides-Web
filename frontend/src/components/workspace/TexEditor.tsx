import Editor, { type Monaco } from "@monaco-editor/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, Download, Loader2, RotateCw, Save, X } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { AgentResponse, Job } from "../../api/types";
import { cn } from "../../lib/utils";
import { useJobStore } from "../../store/jobStore";

export function TexEditor({ job, className }: { job: Job; className?: string }) {
  const queryClient = useQueryClient();
  const proposedEdit = useJobStore((state) => state.proposedEdits[job.id]);
  const setProposedEdit = useJobStore((state) => state.setProposedEdit);
  const [value, setValue] = useState(job.texContent ?? "");
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    setValue(job.texContent ?? "");
    setDirty(false);
  }, [job.id, job.texContent]);

  const saveMutation = useMutation({
    mutationFn: () => api.saveTex(job.id, value),
    onSuccess: async () => {
      setDirty(false);
      await queryClient.invalidateQueries({ queryKey: ["job", job.id] });
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  const compileMutation = useMutation({
    mutationFn: async () => {
      if (dirty) await api.saveTex(job.id, value);
      return api.compileTex(job.id);
    },
    onSuccess: async () => {
      setDirty(false);
      await queryClient.invalidateQueries({ queryKey: ["job", job.id] });
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  const downloadAllMutation = useMutation({
    mutationFn: async () => {
      if (dirty) await api.saveTex(job.id, value);
      return api.downloadAll(job.id);
    },
    onSuccess: async (blob) => {
      setDirty(false);
      await queryClient.invalidateQueries({ queryKey: ["job", job.id] });
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${safeDownloadName(job.title)}-tex-bundle.zip`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    },
  });

  const applyEditMutation = useMutation({
    mutationFn: async () => {
      if (!proposedEdit) throw new Error("No proposed edit to apply");
      return api.applyAgentEdit(job.id, proposedEdit.editId);
    },
    onSuccess: async (nextJob) => {
      setValue(nextJob.texContent ?? value);
      setDirty(false);
      setProposedEdit(job.id, null);
      await queryClient.invalidateQueries({ queryKey: ["job", job.id] });
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  return (
    <div className={cn("flex min-h-0 flex-col overflow-hidden rounded-md border bg-white", className)}>
      <div className="flex items-center justify-between border-b px-3 py-2">
        <div>
          <div className="text-sm font-medium">Beamer TEX</div>
          <div className="text-xs text-slate-500">{dirty ? "Unsaved changes" : "Saved"}</div>
        </div>
        <div className="flex gap-2">
          <button
            className="flex h-8 items-center gap-2 rounded-md border px-3 text-sm hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
            disabled={downloadAllMutation.isPending || (!job.artifacts?.tex && !job.texContent && !value)}
            onClick={() => downloadAllMutation.mutate()}
            title="Download All"
          >
            {downloadAllMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            Download All
          </button>
          <button
            className="flex h-8 items-center gap-2 rounded-md border px-3 text-sm hover:bg-muted disabled:opacity-50"
            disabled={!dirty || saveMutation.isPending}
            onClick={() => saveMutation.mutate()}
          >
            {saveMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            Save
          </button>
          <button
            className="flex h-8 items-center gap-2 rounded-md bg-slate-950 px-3 text-sm text-white disabled:opacity-50"
            disabled={compileMutation.isPending}
            onClick={() => compileMutation.mutate()}
          >
            {compileMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCw className="h-4 w-4" />}
            Recompile
          </button>
        </div>
      </div>
      {compileMutation.isPending ? (
        <div className="border-b bg-amber-50 px-3 py-2 text-xs text-amber-800">Compiler is running. The PDF preview will refresh when it finishes.</div>
      ) : null}
      {downloadAllMutation.error ? (
        <div className="border-b bg-red-50 px-3 py-2 text-xs text-red-700">
          {downloadAllMutation.error instanceof Error ? downloadAllMutation.error.message : "Download failed"}
        </div>
      ) : null}
      {proposedEdit ? (
        <AgentChangeReview
          currentTex={value}
          isApplying={applyEditMutation.isPending}
          onAccept={() => applyEditMutation.mutate()}
          onReject={() => setProposedEdit(job.id, null)}
          proposedEdit={proposedEdit}
        />
      ) : null}
      <div className="min-h-[460px] flex-1">
        <Editor
          defaultLanguage="latex"
          beforeMount={configureLatexLanguage}
          theme="vs"
          value={value}
          onChange={(next) => {
            setValue(next ?? "");
            setDirty(true);
          }}
          options={{
            minimap: { enabled: false },
            wordWrap: "on",
            fontSize: 13,
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  );
}

function safeDownloadName(value: string) {
  return (value.trim() || "autoslides").replace(/[\\/:*?"<>|]+/g, "-").slice(0, 120);
}

type ProposedEdit = NonNullable<AgentResponse["proposedEdit"]>;

function AgentChangeReview({
  currentTex,
  isApplying,
  onAccept,
  onReject,
  proposedEdit,
}: {
  currentTex: string;
  isApplying: boolean;
  onAccept: () => void;
  onReject: () => void;
  proposedEdit: ProposedEdit;
}) {
  return (
    <section className="border-b bg-white">
      <div className="flex flex-wrap items-center justify-between gap-3 px-3 py-2">
        <div className="min-w-0">
          <div className="text-sm font-medium">Pending Agent change</div>
          <div className="truncate text-xs text-slate-500">{proposedEdit.summary}</div>
        </div>
        <div className="flex gap-2">
          <button className="flex h-8 items-center gap-2 rounded-md border px-3 text-sm hover:bg-muted" onClick={onReject}>
            <X className="h-4 w-4" />
            Reject
          </button>
          <button
            className="flex h-8 items-center gap-2 rounded-md bg-slate-950 px-3 text-sm text-white disabled:cursor-not-allowed disabled:opacity-50"
            disabled={isApplying}
            onClick={onAccept}
          >
            {isApplying ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
            Accept change
          </button>
        </div>
      </div>
      <div className="border-t bg-muted/50 p-3">
        <InlineDiffView currentTex={currentTex} proposedTex={proposedEdit.proposedTex ?? currentTex} />
      </div>
    </section>
  );
}

function InlineDiffView({ currentTex, proposedTex }: { currentTex: string; proposedTex: string }) {
  const rows = buildInlineDiffRows(currentTex, proposedTex);
  const additions = rows.filter((row) => row.type === "add").length;
  const removals = rows.filter((row) => row.type === "remove").length;
  return (
    <div className="overflow-hidden rounded-md border bg-white">
      <div className="flex items-center justify-between gap-3 border-b bg-slate-50 px-3 py-2">
        <div className="min-w-0">
          <div className="text-xs font-medium text-slate-700">output.tex</div>
          <div className="text-[11px] text-slate-500">Review proposed changes before applying</div>
        </div>
        <div className="flex shrink-0 items-center gap-2 text-xs">
          <span className="rounded bg-emerald-100 px-2 py-0.5 text-emerald-700">+{additions}</span>
          <span className="rounded bg-red-100 px-2 py-0.5 text-red-700">-{removals}</span>
        </div>
      </div>
      <div className="max-h-64 overflow-auto font-mono text-xs leading-5">
        {rows.map((row, index) => (
          row.type === "hunk" ? (
            <div key={`hunk-${index}`} className="border-y bg-slate-50 px-3 py-1 text-[11px] text-slate-500">
              {row.label}
            </div>
          ) : (
            <div
              key={`${row.text}-${row.type}-${index}`}
              className={cn(
                "grid grid-cols-[44px_44px_22px_1fr] whitespace-pre-wrap",
                row.type === "add" && "bg-emerald-50 text-emerald-900",
                row.type === "remove" && "bg-red-50 text-red-900",
                row.type === "same" && "text-slate-700",
              )}
            >
              <span className="select-none border-r px-2 text-right text-slate-400">{row.oldLine ?? ""}</span>
              <span className="select-none border-r px-2 text-right text-slate-400">{row.newLine ?? ""}</span>
              <span
                className={cn(
                  "select-none px-2 text-center",
                  row.type === "add" && "text-emerald-700",
                  row.type === "remove" && "text-red-700",
                )}
              >
                {row.type === "add" ? "+" : row.type === "remove" ? "-" : ""}
              </span>
              <span className={cn("pr-3", row.type === "remove" && "line-through decoration-red-400")}>{row.text || " "}</span>
            </div>
          )
        ))}
      </div>
    </div>
  );
}

type DiffRow = {
  type: "same" | "add" | "remove";
  text: string;
  oldLine?: number;
  newLine?: number;
};

type RenderDiffRow = DiffRow | { type: "hunk"; label: string };

function buildInlineDiffRows(currentTex: string, proposedTex: string): RenderDiffRow[] {
  const rows = buildDiffRows(currentTex, proposedTex);
  const changedIndexes = rows.map((row, index) => (row.type === "same" ? -1 : index)).filter((index) => index >= 0);
  if (!changedIndexes.length) {
    return [{ type: "hunk", label: "No changes detected" }];
  }

  const context = 4;
  const include = new Set<number>();
  for (const index of changedIndexes) {
    for (let next = Math.max(0, index - context); next <= Math.min(rows.length - 1, index + context); next += 1) {
      include.add(next);
    }
  }

  const rendered: RenderDiffRow[] = [];
  let index = 0;
  while (index < rows.length) {
    if (!include.has(index)) {
      const start = index;
      while (index < rows.length && !include.has(index)) index += 1;
      const hidden = index - start;
      if (rendered.length && index < rows.length) {
        rendered.push({ type: "hunk", label: `@@ ${hidden} unchanged line${hidden === 1 ? "" : "s"} hidden @@` });
      }
      continue;
    }
    rendered.push(rows[index]);
    index += 1;
  }
  return rendered;
}

function buildDiffRows(currentTex: string, proposedTex: string): DiffRow[] {
  const current = currentTex.split("\n");
  const proposed = proposedTex.split("\n");
  const table = Array.from({ length: current.length + 1 }, () => Array<number>(proposed.length + 1).fill(0));

  for (let i = current.length - 1; i >= 0; i -= 1) {
    for (let j = proposed.length - 1; j >= 0; j -= 1) {
      table[i][j] = current[i] === proposed[j] ? table[i + 1][j + 1] + 1 : Math.max(table[i + 1][j], table[i][j + 1]);
    }
  }

  const rows: DiffRow[] = [];
  let i = 0;
  let j = 0;
  let oldLine = 1;
  let newLine = 1;
  while (i < current.length && j < proposed.length) {
    if (current[i] === proposed[j]) {
      rows.push({ type: "same", text: proposed[j], oldLine, newLine });
      i += 1;
      j += 1;
      oldLine += 1;
      newLine += 1;
    } else if (table[i][j + 1] >= table[i + 1][j]) {
      rows.push({ type: "add", text: proposed[j], newLine });
      j += 1;
      newLine += 1;
    } else {
      rows.push({ type: "remove", text: current[i], oldLine });
      i += 1;
      oldLine += 1;
    }
  }

  while (j < proposed.length) {
    rows.push({ type: "add", text: proposed[j], newLine });
    j += 1;
    newLine += 1;
  }
  while (i < current.length) {
    rows.push({ type: "remove", text: current[i], oldLine });
    i += 1;
    oldLine += 1;
  }

  return rows;
}

function configureLatexLanguage(monaco: Monaco) {
  const exists = monaco.languages.getLanguages().some((language: { id: string }) => language.id === "latex");
  if (!exists) {
    monaco.languages.register({ id: "latex" });
  }

  monaco.languages.setLanguageConfiguration("latex", {
    comments: {
      lineComment: "%",
    },
    brackets: [
      ["{", "}"],
      ["[", "]"],
      ["(", ")"],
    ],
    autoClosingPairs: [
      { open: "{", close: "}" },
      { open: "[", close: "]" },
      { open: "(", close: ")" },
      { open: "$", close: "$" },
    ],
  });

  monaco.languages.setMonarchTokensProvider("latex", {
    tokenizer: {
      root: [
        [/%.*$/, "comment"],
        [/\\(?:documentclass|usepackage|begin|end|title|subtitle|author|date|frametitle|section|subsection)\b/, "keyword"],
        [/\\[a-zA-Z@]+/, "type.identifier"],
        [/\$[^$]*\$/, "string"],
        [/[{}[\]()]/, "@brackets"],
        [/[0-9]+(?:\.[0-9]+)?/, "number"],
      ],
    },
  });
}
