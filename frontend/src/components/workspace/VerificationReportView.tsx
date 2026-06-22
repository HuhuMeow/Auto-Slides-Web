import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Loader2, ShieldAlert } from "lucide-react";
import { api } from "../../api/client";
import type { Job, VerificationReport } from "../../api/types";

export function VerificationReportView({ job, report }: { job: Job; report: VerificationReport }) {
  const queryClient = useQueryClient();
  const repairMutation = useMutation({
    mutationFn: () => api.repairPlan(job.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["job", job.id] });
      await queryClient.invalidateQueries({ queryKey: ["verification", job.id] });
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  return (
    <div className="space-y-4">
      <section className="rounded-md border bg-white p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex gap-3">
            {report.passed ? <CheckCircle2 className="h-6 w-6 text-emerald-600" /> : <ShieldAlert className="h-6 w-6 text-amber-600" />}
            <div>
              <h3 className="font-semibold">{report.passed ? "Verification passed" : "Verification needs attention"}</h3>
              <p className="mt-1 text-sm text-slate-600">{report.summary}</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-semibold">{report.coverageScore ?? 0}%</div>
            <div className="text-xs text-slate-500">coverage score</div>
          </div>
        </div>
        {!report.passed ? (
          <button
            className="mt-4 flex h-9 items-center gap-2 rounded-md bg-slate-950 px-3 text-sm font-medium text-white disabled:opacity-50"
            disabled={repairMutation.isPending}
            onClick={() => repairMutation.mutate()}
          >
            {repairMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            One-click repair
          </button>
        ) : null}
      </section>

      <section className="rounded-md border bg-white p-4">
        <h3 className="text-sm font-semibold">Missing content</h3>
        {report.missingContent.length ? (
          <div className="mt-3 space-y-3">
            {report.missingContent.map((item) => (
              <div key={`${item.area}-${item.missingContent}`} className="rounded-md border p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium">{item.area}</span>
                  <span className="rounded-md bg-muted px-2 py-1 text-xs">{item.importance}</span>
                </div>
                <p className="mt-2 text-sm text-slate-600">{item.missingContent}</p>
                <p className="mt-2 text-sm font-medium">Suggested: {item.suggestedAction}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-2 text-sm text-slate-500">No missing content reported.</p>
        )}
      </section>

      <section className="rounded-md border bg-white p-4">
        <h3 className="text-sm font-semibold">Risks</h3>
        <div className="mt-3 space-y-2">
          {report.risks.map((risk) => (
            <div key={`${risk.type}-${risk.message}`} className="rounded-md border p-3 text-sm">
              <div className="mb-1 flex items-center gap-2">
                <span className="font-medium">{risk.type.replace(/_/g, " ")}</span>
                <span className="rounded-md bg-muted px-2 py-0.5 text-xs">{risk.severity}</span>
              </div>
              <p className="text-slate-600">{risk.message}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
