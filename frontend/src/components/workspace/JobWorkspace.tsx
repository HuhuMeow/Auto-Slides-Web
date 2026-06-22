import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, KeyboardEvent, useState } from "react";
import { api } from "../../api/client";
import type { Job } from "../../api/types";
import { JobProgress } from "../jobs/JobProgress";
import { JobStatusBadge } from "../jobs/JobStatusBadge";
import { AgentPanel } from "./AgentPanel";
import { SlidesPlanView } from "./SlidesPlanView";
import { SpeechScriptView } from "./SpeechScriptView";
import { TexPdfSplitView } from "./TexPdfSplitView";
import { VerificationReportView } from "./VerificationReportView";
import { formatDateTime } from "../../lib/utils";
import { useJobStore } from "../../store/jobStore";
import { Bot, Check, Loader2, PanelRightOpen, Pencil, X } from "lucide-react";

type TabKey = "editor" | "plan" | "verification" | "speech";

const tabs: Array<{ key: TabKey; label: string }> = [
  { key: "editor", label: "TEX + PDF" },
  { key: "plan", label: "Slides Plan" },
  { key: "verification", label: "Verification" },
  { key: "speech", label: "Speech" },
];

export function JobWorkspace({ job }: { job: Job }) {
  const [activeTab, setActiveTab] = useState<TabKey>("editor");
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState(job.title);
  const queryClient = useQueryClient();
  const agentCollapsed = useJobStore((state) => state.agentCollapsed);
  const setAgentCollapsed = useJobStore((state) => state.setAgentCollapsed);
  const renameMutation = useMutation({
    mutationFn: (title: string) => api.updateJobTitle(job.id, title),
    onSuccess: async (updatedJob) => {
      queryClient.setQueryData(["job", job.id], updatedJob);
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
      setEditingTitle(false);
    },
  });
  const planQuery = useQuery({
    queryKey: ["plan", job.id],
    queryFn: () => api.getPresentationPlan(job.id),
    enabled: job.progress >= 40,
  });
  const verificationQuery = useQuery({
    queryKey: ["verification", job.id],
    queryFn: () => api.getVerificationReport(job.id),
    enabled: job.progress >= 55,
  });
  const speechQuery = useQuery({
    queryKey: ["speech", job.id],
    queryFn: () => api.getSpeechScript(job.id),
    enabled: job.status === "succeeded",
  });

  function startEditingTitle() {
    setTitleDraft(job.title);
    setEditingTitle(true);
  }

  function cancelEditingTitle() {
    setTitleDraft(job.title);
    setEditingTitle(false);
  }

  function saveTitle(event?: FormEvent) {
    event?.preventDefault();
    const nextTitle = titleDraft.trim();
    if (!nextTitle || renameMutation.isPending) return;
    if (nextTitle === job.title) {
      setEditingTitle(false);
      return;
    }
    renameMutation.mutate(nextTitle);
  }

  function onTitleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Escape") {
      event.preventDefault();
      cancelEditingTitle();
    }
  }

  return (
    <div className="flex h-screen min-w-0 flex-col">
      <header className="border-b bg-white px-6 py-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex min-w-0 items-center gap-2">
              {editingTitle ? (
                <form className="flex min-w-0 flex-1 items-center gap-2" onSubmit={saveTitle}>
                  <input
                    className="h-9 min-w-0 flex-1 rounded-md border bg-white px-3 text-xl font-semibold outline-none focus:border-slate-400"
                    autoFocus
                    value={titleDraft}
                    onChange={(event) => setTitleDraft(event.target.value)}
                    onKeyDown={onTitleKeyDown}
                  />
                  <button
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border bg-white hover:bg-muted disabled:opacity-50"
                    disabled={!titleDraft.trim() || renameMutation.isPending}
                    title="Save task name"
                    type="submit"
                  >
                    {renameMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                  </button>
                  <button
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border bg-white hover:bg-muted"
                    disabled={renameMutation.isPending}
                    onClick={cancelEditingTitle}
                    title="Cancel rename"
                    type="button"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </form>
              ) : (
                <>
                  <h1 className="truncate text-xl font-semibold">{job.title}</h1>
                  <button
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-slate-500 hover:bg-muted hover:text-slate-900"
                    onClick={startEditingTitle}
                    title="Rename task"
                    type="button"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                </>
              )}
              <JobStatusBadge status={job.status} />
            </div>
            {renameMutation.error ? (
              <div className="mt-2 text-xs text-red-700">
                {renameMutation.error instanceof Error ? renameMutation.error.message : "Failed to rename task"}
              </div>
            ) : null}
            <div className="mt-1 flex flex-wrap gap-3 text-xs text-slate-500">
              <span>Created {formatDateTime(job.createdAt)}</span>
              <span>Updated {formatDateTime(job.updatedAt)}</span>
              {job.paperFileName ? <span>{job.paperFileName}</span> : null}
            </div>
          </div>
          <div className="w-full max-w-md">
            <JobProgress job={job} />
          </div>
        </div>
        {job.status === "failed" && job.error ? (
          <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{job.error}</div>
        ) : null}
      </header>

      <div className="min-h-0 flex-1 overflow-hidden p-4">
        <div className="flex h-full min-h-0 flex-col gap-4 xl:flex-row">
          <section className="min-w-0 flex-1 overflow-hidden rounded-md">
            <div className="mb-3 flex flex-wrap gap-2">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  className={`h-9 rounded-md border px-3 text-sm ${
                    activeTab === tab.key ? "border-slate-950 bg-white font-medium" : "bg-white text-slate-600"
                  }`}
                  onClick={() => setActiveTab(tab.key)}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            <div className="h-[calc(100vh-190px)] overflow-y-auto">
              {activeTab === "editor" ? <TexPdfSplitView job={job} /> : null}
              {activeTab === "plan" ? (
                planQuery.data ? <SlidesPlanView plan={planQuery.data} /> : <EmptyState text="Presentation plan is not ready yet." />
              ) : null}
              {activeTab === "verification" ? (
                verificationQuery.data ? (
                  <VerificationReportView job={job} report={verificationQuery.data} />
                ) : (
                  <EmptyState text="Verification report is not ready yet." />
                )
              ) : null}
              {activeTab === "speech" ? <SpeechScriptView script={speechQuery.data ?? null} /> : null}
            </div>
          </section>
          {agentCollapsed ? (
            <aside className="flex h-full min-h-[620px] w-full shrink-0 flex-col items-center rounded-md border bg-white p-2 xl:w-14">
              <button className="flex h-10 w-10 items-center justify-center rounded-md border hover:bg-muted" onClick={() => setAgentCollapsed(false)} title="Expand Agent panel">
                <PanelRightOpen className="h-4 w-4" />
              </button>
              <div className="mt-3 flex h-10 w-10 items-center justify-center rounded-md bg-muted" title="Editor Agent">
                <Bot className="h-4 w-4" />
              </div>
            </aside>
          ) : (
            <AgentPanel job={job} />
          )}
        </div>
      </div>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return <div className="flex min-h-[360px] items-center justify-center rounded-md border border-dashed bg-white text-sm text-slate-500">{text}</div>;
}
