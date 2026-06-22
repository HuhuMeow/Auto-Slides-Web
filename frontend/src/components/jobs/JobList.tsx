import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FileText, Trash2 } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../../api/client";
import type { Job } from "../../api/types";
import { cn, formatDateTime } from "../../lib/utils";
import { JobStatusBadge } from "./JobStatusBadge";

export function JobList({ jobs }: { jobs: Job[] }) {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteJob(id),
    onSuccess: async (_result, deletedId) => {
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
      if (jobId === deletedId) {
        navigate("/", { replace: true });
      }
    },
  });

  function deleteTask(job: Job) {
    if (deleteMutation.isPending) return;
    const confirmed = window.confirm(`Delete "${job.title}"? This removes it from your task list.`);
    if (confirmed) deleteMutation.mutate(job.id);
  }

  if (!jobs.length) {
    return <div className="rounded-md border border-dashed p-3 text-xs text-slate-500">No tasks yet.</div>;
  }

  return (
    <div className="space-y-2">
      {jobs.map((job) => (
        <div
          key={job.id}
          className={cn(
            "group relative rounded-md border bg-white text-left transition hover:border-slate-300",
            jobId === job.id && "border-slate-950",
          )}
        >
          <Link to={`/jobs/${job.id}`} className="block p-3 pr-10">
            <div className="flex items-start gap-2">
              <FileText className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium">{job.title}</div>
                <div className="mt-1 flex items-center gap-2">
                  <JobStatusBadge status={job.status} compact />
                  <span className="truncate text-[11px] text-slate-500">{formatDateTime(job.updatedAt)}</span>
                </div>
              </div>
            </div>
          </Link>
          <button
            className="absolute right-2 top-2 flex h-7 w-7 items-center justify-center rounded-md text-slate-400 opacity-0 hover:bg-red-50 hover:text-red-700 group-hover:opacity-100 focus:opacity-100 disabled:opacity-50"
            disabled={deleteMutation.isPending}
            onClick={() => deleteTask(job)}
            title="Delete task"
            type="button"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
