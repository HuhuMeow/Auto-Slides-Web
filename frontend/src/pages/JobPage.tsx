import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { JobWorkspace } from "../components/workspace/JobWorkspace";

export function JobPage() {
  const { jobId } = useParams();
  const { data: job, isLoading, error } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => api.getJob(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "running" || status === "queued" ? 1500 : false;
    },
  });

  if (isLoading) return <div className="flex h-screen items-center justify-center text-sm text-slate-500">Loading task...</div>;
  if (error || !job) {
    return (
      <div className="flex h-screen items-center justify-center p-6">
        <div className="rounded-md border bg-white p-6 text-sm text-red-700">Task not found or failed to load.</div>
      </div>
    );
  }

  return <JobWorkspace job={job} />;
}
