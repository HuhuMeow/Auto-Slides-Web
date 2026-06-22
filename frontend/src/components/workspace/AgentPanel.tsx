import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Bot, Loader2, PanelRightClose, Send, UserRound, Wand2 } from "lucide-react";
import { FormEvent, KeyboardEvent, useState } from "react";
import { api } from "../../api/client";
import type { AgentMessage, Job } from "../../api/types";
import { formatDateTime } from "../../lib/utils";
import { useJobStore } from "../../store/jobStore";

export function AgentPanel({ job }: { job: Job }) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const pendingEdit = useJobStore((state) => state.proposedEdits[job.id]);
  const setAgentCollapsed = useJobStore((state) => state.setAgentCollapsed);
  const setProposedEdit = useJobStore((state) => state.setProposedEdit);
  const queryClient = useQueryClient();

  const sendMutation = useMutation({
    mutationFn: (message: string) => api.sendAgentMessage(job.id, message),
    onSuccess: (response) => {
      setMessages((current) => [
        ...current,
        {
          id: response.id,
          role: "agent",
          content: response.message,
          createdAt: new Date().toISOString(),
          response,
        },
      ]);
      setProposedEdit(job.id, response.proposedEdit ?? null);
      void queryClient.invalidateQueries({ queryKey: ["job", job.id] });
    },
  });

  function sendCurrentMessage() {
    const message = input.trim();
    if (!message || sendMutation.isPending) return;
    setMessages((current) => [
      ...current,
      {
        id: `user_${Date.now()}`,
        role: "user",
        content: message,
        createdAt: new Date().toISOString(),
      },
    ]);
    setInput("");
    sendMutation.mutate(message);
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    sendCurrentMessage();
  }

  function onInputKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Enter" || event.shiftKey) return;
    event.preventDefault();
    sendCurrentMessage();
  }

  return (
    <aside className="flex h-full min-h-[620px] w-full flex-col rounded-md border bg-white xl:w-[360px]">
      <div className="border-b p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            <h3 className="font-semibold">Editor Agent</h3>
          </div>
          <button className="rounded-md p-2 hover:bg-muted" onClick={() => setAgentCollapsed(true)} title="Collapse Agent panel">
            <PanelRightClose className="h-4 w-4" />
          </button>
        </div>
        <p className="mt-1 text-xs text-slate-500">Backend TEX editor. Suggestions appear as pending changes in the TEX pane.</p>
      </div>

      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
        {!messages.length ? (
          <div className="rounded-md border border-dashed p-3 text-sm text-slate-500">
            Try: “Add one motivation slide after introduction” or “Reduce text on slide 3”.
          </div>
        ) : null}
        {messages.map((message) => (
          <div key={message.id} className="space-y-2">
            <div className={`flex gap-2 ${message.role === "user" ? "justify-end" : "justify-start"}`}>
              {message.role === "agent" ? <Bot className="mt-1 h-4 w-4 shrink-0" /> : null}
              <div className={`max-w-[88%] rounded-md px-3 py-2 text-sm ${message.role === "user" ? "bg-slate-950 text-white" : "bg-muted"}`}>
                <div>{message.content}</div>
                <div className={`mt-1 text-[10px] ${message.role === "user" ? "text-slate-300" : "text-slate-500"}`}>
                  {formatDateTime(message.createdAt)}
                </div>
              </div>
              {message.role === "user" ? <UserRound className="mt-1 h-4 w-4 shrink-0" /> : null}
            </div>
            {message.response?.analysis ? (
              <div className="ml-6 rounded-md border bg-white p-2 text-xs text-slate-600">{message.response.analysis}</div>
            ) : null}
          </div>
        ))}
        {sendMutation.isPending ? (
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            Agent is preparing a diff...
          </div>
        ) : null}
        {sendMutation.error ? (
          <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {sendMutation.error instanceof Error ? sendMutation.error.message : "Editor Agent failed"}
          </div>
        ) : null}

        {pendingEdit ? (
          <div className="rounded-md border bg-white p-3">
            <div className="mb-2 flex items-center gap-2 text-sm font-medium">
              <Wand2 className="h-4 w-4" />
              Proposed edit
            </div>
            <p className="text-sm text-slate-600">{pendingEdit.summary}</p>
            <p className="mt-2 rounded-md bg-muted px-3 py-2 text-xs text-slate-600">
              Review the current/proposed TEX and red/green diff in the editor pane, then accept or reject the change there.
            </p>
          </div>
        ) : null}
      </div>

      <form className="border-t p-3" onSubmit={onSubmit}>
        <div className="flex gap-2">
          <textarea
            className="min-h-20 flex-1 resize-none rounded-md border px-3 py-2 text-sm outline-none focus:border-slate-400"
            placeholder="Ask the Editor Agent to revise this deck..."
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={onInputKeyDown}
          />
          <button
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-slate-950 text-white disabled:opacity-50"
            disabled={!input.trim() || sendMutation.isPending}
            type="submit"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>
    </aside>
  );
}
