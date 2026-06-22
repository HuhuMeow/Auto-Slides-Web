import type { Job } from "../../api/types";
import { PdfPreview } from "./PdfPreview";
import { TexEditor } from "./TexEditor";
import { type CSSProperties, type PointerEvent as ReactPointerEvent, useRef, useState } from "react";

export function TexPdfSplitView({ job }: { job: Job }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const draggingRef = useRef(false);
  const frameRef = useRef<number | null>(null);
  const [dragging, setDragging] = useState(false);
  const [leftPanePx, setLeftPanePx] = useState<number | null>(null);

  function getPaneBounds() {
    const container = containerRef.current;
    if (!container) return null;
    const rect = container.getBoundingClientRect();
    return {
      left: rect.left,
      max: Math.max(420, rect.width - 340),
      min: Math.min(520, Math.max(320, rect.width * 0.28)),
      width: rect.width,
    };
  }

  function updateFromPointer(clientX: number) {
    const bounds = getPaneBounds();
    if (!bounds) return;
    const nextPx = Math.min(bounds.max, Math.max(bounds.min, clientX - bounds.left - 5));

    if (frameRef.current !== null) {
      cancelAnimationFrame(frameRef.current);
    }
    frameRef.current = requestAnimationFrame(() => {
      setLeftPanePx(nextPx);
      frameRef.current = null;
    });
  }

  function beginDrag(event: ReactPointerEvent<HTMLDivElement>) {
    if (event.button !== 0) return;
    event.preventDefault();
    event.currentTarget.setPointerCapture(event.pointerId);
    draggingRef.current = true;
    setDragging(true);
    updateFromPointer(event.clientX);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }

  function moveDrag(event: ReactPointerEvent<HTMLDivElement>) {
    if (!draggingRef.current || event.buttons !== 1) return;
    event.preventDefault();
    updateFromPointer(event.clientX);
  }

  function endDrag(event: ReactPointerEvent<HTMLDivElement>) {
    if (!draggingRef.current) return;
    draggingRef.current = false;
    setDragging(false);
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
  }

  return (
    <div
      ref={containerRef}
      className="grid h-full min-h-[620px] grid-cols-1 gap-3 xl:grid-cols-[minmax(320px,var(--left-pane))_12px_minmax(320px,1fr)] xl:gap-0"
      style={{ "--left-pane": leftPanePx ? `${leftPanePx}px` : "55%" } as CSSProperties}
    >
      <TexEditor job={job} className="h-full" />
      <div
        aria-label="Resize TEX and PDF panes"
        aria-valuenow={leftPanePx ?? undefined}
        className="group relative hidden cursor-col-resize touch-none items-center justify-center xl:flex"
        onPointerDown={beginDrag}
        onPointerMove={moveDrag}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
        role="separator"
      >
        <div className="absolute inset-y-0 left-1/2 w-8 -translate-x-1/2" />
        <div className={`h-20 w-1 rounded-full transition ${dragging ? "bg-slate-950" : "bg-slate-300 group-hover:bg-slate-500"}`} />
      </div>
      <PdfPreview job={job} className={`h-full min-h-[620px] ${dragging ? "pointer-events-none" : ""}`} />
    </div>
  );
}
