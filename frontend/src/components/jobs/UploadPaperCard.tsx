import { ChangeEvent, DragEvent, useState } from "react";
import { FileUp, X } from "lucide-react";
import { formatBytes } from "../../lib/utils";

export function UploadPaperCard({
  file,
  onFileChange,
}: {
  file: File | null;
  onFileChange: (file: File | null) => void;
}) {
  const [dragging, setDragging] = useState(false);

  function acceptFile(nextFile?: File) {
    if (!nextFile) return;
    if (nextFile.type !== "application/pdf" && !nextFile.name.toLowerCase().endsWith(".pdf")) return;
    onFileChange(nextFile);
  }

  function onDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setDragging(false);
    acceptFile(event.dataTransfer.files[0]);
  }

  function onSelect(event: ChangeEvent<HTMLInputElement>) {
    acceptFile(event.target.files?.[0]);
  }

  return (
    <div className="space-y-3">
      <label
        className={`flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed bg-white p-5 text-center transition ${
          dragging ? "border-slate-950 bg-muted" : "border-slate-300"
        }`}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <FileUp className="mb-3 h-8 w-8 text-slate-500" />
        <span className="text-sm font-medium">Drop a PDF here or choose a file</span>
        <span className="mt-1 text-xs text-slate-500">Only .pdf files are accepted in the MVP.</span>
        <input className="hidden" type="file" accept="application/pdf,.pdf" onChange={onSelect} />
      </label>

      {file ? (
        <div className="flex items-center justify-between rounded-md border bg-white px-3 py-2">
          <div className="min-w-0">
            <div className="truncate text-sm font-medium">{file.name}</div>
            <div className="text-xs text-slate-500">{formatBytes(file.size)}</div>
          </div>
          <button className="rounded-md p-1 hover:bg-muted" onClick={() => onFileChange(null)} type="button">
            <X className="h-4 w-4" />
          </button>
        </div>
      ) : null}
    </div>
  );
}
