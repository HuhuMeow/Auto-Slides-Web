import { Mic2 } from "lucide-react";
import type { SpeechScript } from "../../api/types";

export function SpeechScriptView({ script }: { script: SpeechScript | null }) {
  if (!script) {
    return (
      <div className="flex min-h-[360px] flex-col items-center justify-center rounded-md border border-dashed bg-white text-center">
        <Mic2 className="mb-3 h-8 w-8 text-slate-400" />
        <div className="text-sm font-medium">Speech script was not generated</div>
        <p className="mt-1 max-w-sm text-sm text-slate-500">Enable speech generation when creating a task to see a script here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <section className="rounded-md border bg-white p-4">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Speech script</div>
        <h2 className="mt-2 text-lg font-semibold">{script.title}</h2>
        <p className="mt-1 text-sm text-slate-500">
          {script.targetDurationMinutes} minutes · {script.style.replace(/_/g, " ")}
        </p>
      </section>
      {script.sections.map((section) => (
        <section key={section.slideNumber} className="rounded-md border bg-white p-4">
          <div className="flex items-center justify-between gap-3">
            <h3 className="font-semibold">
              {section.slideNumber > 0 ? `Slide ${section.slideNumber}: ` : ""}
              {section.slideTitle}
            </h3>
            <span className="rounded-md border px-2 py-1 text-xs">{section.duration}</span>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-700">{section.script}</p>
          {section.speakerNotes?.length ? (
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-500">
              {section.speakerNotes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          ) : null}
        </section>
      ))}
    </div>
  );
}
