import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, X } from "lucide-react";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { DEFAULT_CONFIG, type ConversionConfig } from "../../api/types";
import { useJobStore } from "../../store/jobStore";
import { ConversionConfigForm } from "./ConversionConfigForm";
import { UploadPaperCard } from "./UploadPaperCard";

export function NewJobPanel() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const open = useJobStore((state) => state.newJobOpen);
  const setOpen = useJobStore((state) => state.setNewJobOpen);
  const [file, setFile] = useState<File | null>(null);
  const [config, setConfig] = useState<ConversionConfig>(DEFAULT_CONFIG);
  const { data: themes = [] } = useQuery({ queryKey: ["themes"], queryFn: api.listThemes });
  const { data: models } = useQuery({ queryKey: ["models"], queryFn: api.listModels });
  const disabled = !file;

  const title = useMemo(() => file?.name.replace(/\.pdf$/i, "") ?? "", [file]);

  const createMutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error("PDF file is required");
      const job = await api.createJob({ file, fileName: file.name, fileSize: file.size, title, config });
      return api.startJob(job.id);
    },
    onSuccess: async (job) => {
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
      setOpen(false);
      setFile(null);
      navigate(`/jobs/${job.id}`);
    },
  });

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/20">
      <div className="flex h-full w-full max-w-xl flex-col border-l bg-[#f7f7f8] shadow-xl">
        <div className="flex items-center justify-between border-b bg-white px-5 py-4">
          <div>
            <h2 className="text-base font-semibold">New conversion task</h2>
            <p className="text-sm text-slate-500">Use mock API now; preserve the same adapter for FastAPI later.</p>
          </div>
          <button className="rounded-md p-2 hover:bg-muted" onClick={() => setOpen(false)}>
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="min-h-0 flex-1 space-y-6 overflow-y-auto p-5">
          <section className="space-y-3">
            <div>
              <h3 className="text-sm font-semibold">1. Upload paper PDF</h3>
              <p className="text-xs text-slate-500">The mock API stores only file metadata.</p>
            </div>
            <UploadPaperCard file={file} onFileChange={setFile} />
          </section>

          <section className="space-y-3">
            <div>
              <h3 className="text-sm font-semibold">2. Configure conversion</h3>
              <p className="text-xs text-slate-500">These fields map directly to the future backend contract.</p>
            </div>
            <ConversionConfigForm config={config} themes={themes} models={models} onChange={setConfig} />
          </section>
        </div>

        <div className="border-t bg-white p-4">
          {createMutation.error ? (
            <div className="mb-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {createMutation.error instanceof Error ? createMutation.error.message : "Failed to create task"}
            </div>
          ) : null}
          <button
            className="flex h-10 w-full items-center justify-center gap-2 rounded-md bg-slate-950 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
            disabled={disabled || createMutation.isPending}
            onClick={() => createMutation.mutate()}
          >
            {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Start conversion
          </button>
        </div>
      </div>
    </div>
  );
}
