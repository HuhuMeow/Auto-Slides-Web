import type { PresentationPlan, SlidePlan } from "../../api/types";

export function SlidesPlanView({
  plan,
  onEditSlide,
  onReorderSlides,
}: {
  plan: PresentationPlan;
  onEditSlide?: (slide: SlidePlan) => void;
  onReorderSlides?: (slides: SlidePlan[]) => void;
}) {
  void onEditSlide;
  void onReorderSlides;

  return (
    <div className="space-y-4">
      <section className="rounded-md border bg-white p-4">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Paper</div>
        <h2 className="mt-2 text-lg font-semibold">{plan.paperInfo.title}</h2>
        <p className="mt-2 text-sm text-slate-600">{plan.paperInfo.abstract}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {plan.paperInfo.authors.map((author) => (
            <span key={author} className="rounded-md bg-muted px-2 py-1 text-xs text-slate-600">
              {author}
            </span>
          ))}
        </div>
      </section>

      <section className="grid gap-3">
        {plan.slidesPlan.map((slide) => (
          <article key={slide.slideNumber} className="rounded-md border bg-white p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="text-xs font-medium text-slate-500">Slide {slide.slideNumber}</div>
                <h3 className="mt-1 text-base font-semibold">{slide.title}</h3>
              </div>
              <div className="flex items-center gap-2">
                <span className="rounded-md border bg-muted px-2 py-1 text-xs">{slide.slideType}</span>
                {slide.estimatedTime ? <span className="rounded-md border px-2 py-1 text-xs">{slide.estimatedTime}</span> : null}
              </div>
            </div>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-700">
              {slide.content.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            {slide.figureReference ? (
              <div className="mt-3 rounded-md border bg-muted p-3 text-sm">
                <div className="font-medium">Figure: {slide.figureReference.filename}</div>
                {slide.figureReference.caption ? <div className="mt-1 text-slate-600">{slide.figureReference.caption}</div> : null}
              </div>
            ) : null}
          </article>
        ))}
      </section>
    </div>
  );
}
