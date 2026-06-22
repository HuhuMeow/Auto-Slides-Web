import type { Job, JobEvent } from "../../api/types";

function formatRemainingTime(seconds?: number | null) {
  if (!seconds || seconds <= 0) return null;
  if (seconds < 60) return "ETA <1 min";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `ETA ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return remainingMinutes > 0 ? `ETA ${hours}h ${remainingMinutes}m` : `ETA ${hours}h`;
}

function eventTone(level: JobEvent["level"]) {
  if (level === "error") return "bg-red-500";
  if (level === "warning") return "bg-amber-500";
  if (level === "success") return "bg-emerald-500";
  return "bg-slate-400";
}

export function JobProgress({ job }: { job: Job }) {
  const eta = formatRemainingTime(job.estimatedRemainingSeconds);
  const currentEvent = job.events?.[job.events.length - 1];
  const currentAgent = currentEvent?.agent ?? "Pipeline";
  const currentMessage = currentEvent?.message ?? job.message;
  const currentLevel = currentEvent?.level ?? "info";

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>{job.stage?.replace(/_/g, " ") || "not started"}</span>
        <span className="flex items-center gap-2">
          {eta ? <span>{eta}</span> : null}
          <span>{job.progress}%</span>
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-slate-950 transition-all duration-500" style={{ width: `${job.progress}%` }} />
      </div>
      {currentMessage ? (
        <p className="flex min-w-0 items-center gap-2 text-xs text-slate-600" aria-live="polite">
          <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${eventTone(currentLevel)}`} />
          <span className="truncate" title={`${currentAgent}：${currentMessage}`}>
            <span className="font-medium text-slate-800">{currentAgent}：</span>
            {currentMessage}
          </span>
        </p>
      ) : null}
    </div>
  );
}
