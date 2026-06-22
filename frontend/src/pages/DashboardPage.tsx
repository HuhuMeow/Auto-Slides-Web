import { Plus, Presentation, ShieldCheck, Wand2 } from "lucide-react";
import type { ReactNode } from "react";
import { useJobStore } from "../store/jobStore";

export function DashboardPage() {
  const setNewJobOpen = useJobStore((state) => state.setNewJobOpen);

  return (
    <div className="flex h-screen items-center justify-center p-6">
      <div className="w-full max-w-3xl rounded-lg border bg-white p-8 shadow-subtle">
        <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-md bg-slate-950 text-white">
          <Presentation className="h-6 w-6" />
        </div>
        <h1 className="text-2xl font-semibold">Auto-Slides workspace</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Create a mock conversion task, review structured presentation output, inspect generated TEX, and test the
          Editor Agent flow before the Python backend is exposed as a web service.
        </p>

        <div className="mt-6 grid gap-3 md:grid-cols-3">
          <Feature icon={<Presentation className="h-4 w-4" />} title="Paper to Beamer" text="Mock conversion pipeline with stages and artifacts." />
          <Feature icon={<ShieldCheck className="h-4 w-4" />} title="QA visible" text="Verification and repair are first-class UI states." />
          <Feature icon={<Wand2 className="h-4 w-4" />} title="Agent edits" text="Natural language requests produce confirmable diffs." />
        </div>

        <button
          className="mt-8 flex h-10 items-center gap-2 rounded-md bg-slate-950 px-4 text-sm font-medium text-white"
          onClick={() => setNewJobOpen(true)}
        >
          <Plus className="h-4 w-4" />
          New conversion task
        </button>
      </div>
    </div>
  );
}

function Feature({ icon, title, text }: { icon: ReactNode; title: string; text: string }) {
  return (
    <div className="rounded-md border p-4">
      <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-md bg-muted">{icon}</div>
      <div className="text-sm font-semibold">{title}</div>
      <p className="mt-1 text-sm text-slate-500">{text}</p>
    </div>
  );
}
