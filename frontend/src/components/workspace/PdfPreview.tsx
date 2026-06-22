import { Download, FileText } from "lucide-react";
import { useEffect, useState } from "react";
import type { Job } from "../../api/types";
import { cn } from "../../lib/utils";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const TOKEN_KEY = "autoslides.http.token";

function resolveArtifactUrl(url: string) {
  if (/^https?:\/\//i.test(url)) return url;
  return `${API_BASE_URL}${url.startsWith("/") ? url : `/${url}`}`;
}

export function PdfPreview({ job, className }: { job: Job; className?: string }) {
  const pdf = job.artifacts?.pdf;
  const pdfUrl = pdf?.url;
  const pdfVersion = pdf?.createdAt || job.updatedAt;
  const realBackend = import.meta.env.VITE_USE_MOCK_API === "false";
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  useEffect(() => {
    if (!pdfUrl) {
      setPreviewUrl(null);
      setPreviewError(null);
      setLoadingPreview(false);
      return;
    }

    if (!realBackend) {
      setPreviewUrl("/placeholder-slides.html");
      setPreviewError(null);
      setLoadingPreview(false);
      return;
    }

    let cancelled = false;
    let objectUrl: string | null = null;
    const artifactUrl = pdfUrl;
    async function loadPdf() {
      setLoadingPreview(true);
      setPreviewError(null);
      try {
        const token = localStorage.getItem(TOKEN_KEY);
        const response = await fetch(resolveArtifactUrl(artifactUrl), {
          cache: "no-store",
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        });
        if (!response.ok) {
          throw new Error(`PDF artifact request failed: ${response.status}`);
        }
        const blob = await response.blob();
        objectUrl = URL.createObjectURL(blob);
        if (!cancelled) {
          setPreviewUrl(objectUrl);
        }
      } catch (error) {
        if (!cancelled) {
          setPreviewUrl(null);
          setPreviewError(error instanceof Error ? error.message : "Failed to load PDF preview");
        }
      } finally {
        if (!cancelled) setLoadingPreview(false);
      }
    }

    loadPdf();
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [pdfUrl, pdfVersion, realBackend]);

  const frameUrl = previewUrl && realBackend ? `${previewUrl}#toolbar=0&navpanes=0&scrollbar=0&view=FitH` : previewUrl;

  if (!pdf) {
    return (
      <div className={cn("flex min-h-[520px] flex-col items-center justify-center rounded-md border border-dashed bg-white text-center", className)}>
        <FileText className="mb-3 h-8 w-8 text-slate-400" />
        <div className="text-sm font-medium">PDF preview is not ready</div>
        <p className="mt-1 max-w-sm text-sm text-slate-500">
          The mock job will attach a PDF artifact when compilation reaches 100%.
        </p>
      </div>
    );
  }

  return (
    <div className={cn("flex h-[calc(100vh-220px)] min-h-[520px] flex-col overflow-hidden rounded-md border bg-white", className)}>
      <div className="flex items-center justify-between border-b px-3 py-2">
        <div>
          <div className="text-sm font-medium">PDF Preview</div>
          <div className="text-xs text-slate-500">{pdf.name}</div>
        </div>
        <div className="flex items-center gap-1">
          {previewUrl ? (
            <a
              className="flex h-8 w-8 items-center justify-center rounded-md border hover:bg-muted"
              download={pdf.name || "slides.pdf"}
              href={previewUrl}
              title="Download PDF"
            >
              <Download className="h-4 w-4" />
            </a>
          ) : null}
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-auto bg-slate-100">
        <div className="relative h-full min-h-[620px] bg-white">
          {loadingPreview ? (
            <div className="absolute inset-0 flex items-center justify-center text-sm text-slate-500">Loading PDF preview...</div>
          ) : null}
          {previewError ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-center">
              <FileText className="h-8 w-8 text-slate-400" />
              <div className="text-sm font-medium">PDF preview failed to load</div>
              <div className="max-w-sm text-sm text-slate-500">{previewError}</div>
            </div>
          ) : null}
          {frameUrl ? <iframe className="h-full w-full border-0" title="Generated slide PDF preview" src={frameUrl} /> : null}
        </div>
      </div>
    </div>
  );
}
