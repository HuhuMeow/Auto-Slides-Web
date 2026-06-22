import type { JobStatus } from "../../api/types";
import { cn } from "../../lib/utils";

const styles: Record<JobStatus, string> = {
  draft: "bg-slate-100 text-slate-600 border-slate-200",
  queued: "bg-blue-50 text-blue-700 border-blue-200",
  running: "bg-amber-50 text-amber-700 border-amber-200",
  waiting_user_input: "bg-purple-50 text-purple-700 border-purple-200",
  succeeded: "bg-emerald-50 text-emerald-700 border-emerald-200",
  failed: "bg-red-50 text-red-700 border-red-200",
  cancelled: "bg-slate-100 text-slate-500 border-slate-200",
};

export function JobStatusBadge({ status, compact = false }: { status: JobStatus; compact?: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium",
        compact && "px-1.5 py-0 text-[11px]",
        styles[status],
      )}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}
