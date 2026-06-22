import type { ConversionConfig, LlmProvider, ModelOption, ThemeOption } from "../../api/types";

const fallbackModels: ModelOption[] = [
  { provider: "deepseek", model: "deepseek-chat", label: "deepseek-chat", configured: true, default: true },
  { provider: "deepseek", model: "deepseek-reasoner", label: "deepseek-reasoner", configured: true, default: false },
  { provider: "openrouter", model: "openai/gpt-4o", label: "openai/gpt-4o", configured: true, default: false },
  { provider: "openrouter", model: "openai/gpt-4.1", label: "openai/gpt-4.1", configured: true, default: false },
  { provider: "openrouter", model: "openai/gpt-4.1-mini", label: "openai/gpt-4.1-mini", configured: true, default: false },
  { provider: "openrouter", model: "openai/o4-mini", label: "openai/o4-mini", configured: true, default: false },
];
const providerLabels: Record<LlmProvider, string> = {
  deepseek: "DeepSeek",
  openrouter: "ChatGPT / OpenRouter",
};
const speechStyles = [
  { value: "academic_conference", label: "Academic conference" },
  { value: "classroom", label: "Classroom" },
  { value: "industry_presentation", label: "Industry presentation" },
  { value: "public_talk", label: "Public talk" },
] as const;

export function ConversionConfigForm({
  config,
  themes,
  models = fallbackModels,
  onChange,
}: {
  config: ConversionConfig;
  themes: ThemeOption[];
  models?: ModelOption[];
  onChange: (config: ConversionConfig) => void;
}) {
  const provider = config.provider ?? "deepseek";
  const activeModels = models.filter((model) => model.provider === provider);

  function patch(next: Partial<ConversionConfig>) {
    onChange({ ...config, ...next });
  }

  function changeProvider(nextProvider: LlmProvider) {
    const nextModel = models.find((model) => model.provider === nextProvider && model.default) ?? models.find((model) => model.provider === nextProvider);
    patch({ provider: nextProvider, model: nextModel?.model ?? config.model });
  }

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-3">
        <label className="space-y-2">
          <span className="text-sm font-medium">Output language</span>
          <select
            className="h-10 w-full rounded-md border bg-white px-3 text-sm"
            value={config.language}
            onChange={(event) => patch({ language: event.target.value as ConversionConfig["language"] })}
          >
            <option value="en">English</option>
            <option value="zh">Chinese</option>
          </select>
        </label>
        <label className="space-y-2">
          <span className="text-sm font-medium">Provider</span>
          <select
            className="h-10 w-full rounded-md border bg-white px-3 text-sm"
            value={provider}
            onChange={(event) => changeProvider(event.target.value as LlmProvider)}
          >
            {(Object.keys(providerLabels) as LlmProvider[]).map((providerKey) => (
              <option key={providerKey} value={providerKey}>
                {providerLabels[providerKey]}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="space-y-2">
        <span className="text-sm font-medium">Model</span>
        <select
          className="h-10 w-full rounded-md border bg-white px-3 text-sm"
          value={config.model}
          onChange={(event) => patch({ model: event.target.value })}
        >
          {activeModels.map((model) => (
            <option key={`${model.provider}:${model.model}`} value={model.model}>
              {model.label}
              {model.configured ? "" : " (not configured)"}
            </option>
          ))}
        </select>
      </label>

      <label className="space-y-2">
        <span className="text-sm font-medium">Beamer theme</span>
        <select
          className="h-10 w-full rounded-md border bg-white px-3 text-sm"
          value={config.theme}
          onChange={(event) => patch({ theme: event.target.value })}
        >
          {themes.map((theme) => (
            <option key={theme.name} value={theme.name}>
              {theme.name}
            </option>
          ))}
        </select>
      </label>

      <div className="grid grid-cols-2 gap-3">
        {themes.slice(0, 4).map((theme) => (
          <button
            key={theme.name}
            className={`overflow-hidden rounded-md border bg-white text-left ${
              config.theme === theme.name ? "border-slate-950" : "border-slate-200"
            }`}
            onClick={() => patch({ theme: theme.name })}
            type="button"
          >
            <img className="h-20 w-full object-cover" src={theme.previewUrl} alt={`${theme.name} theme preview`} />
            <div className="px-2 py-1.5 text-xs font-medium">{theme.name}</div>
          </button>
        ))}
      </div>

      <div className="space-y-2 rounded-md border bg-white p-3">
        <ToggleRow
          label="LLM enhancement"
          checked={config.enableLlmEnhancement}
          onChange={(checked) => patch({ enableLlmEnhancement: checked })}
        />
        <ToggleRow
          label="Coverage verification"
          checked={config.enableVerification}
          onChange={(checked) => patch({ enableVerification: checked })}
        />
        <ToggleRow
          label="Automatic repair"
          checked={config.enableAutoRepair}
          onChange={(checked) => patch({ enableAutoRepair: checked })}
        />
        <ToggleRow
          label="Skip PDF compilation"
          checked={config.skipCompilation}
          onChange={(checked) => patch({ skipCompilation: checked })}
        />
        <ToggleRow
          label="Generate speech script"
          checked={config.enableSpeech}
          onChange={(checked) => patch({ enableSpeech: checked })}
        />
      </div>

      {config.enableSpeech ? (
        <div className="grid grid-cols-2 gap-3">
          <label className="space-y-2">
            <span className="text-sm font-medium">Duration</span>
            <input
              className="h-10 w-full rounded-md border bg-white px-3 text-sm"
              min={5}
              max={90}
              type="number"
              value={config.speechDuration}
              onChange={(event) => patch({ speechDuration: Number(event.target.value) })}
            />
          </label>
          <label className="space-y-2">
            <span className="text-sm font-medium">Speech style</span>
            <select
              className="h-10 w-full rounded-md border bg-white px-3 text-sm"
              value={config.speechStyle}
              onChange={(event) => patch({ speechStyle: event.target.value as ConversionConfig["speechStyle"] })}
            >
              {speechStyles.map((style) => (
                <option key={style.value} value={style.value}>
                  {style.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      ) : null}
    </div>
  );
}

function ToggleRow({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between gap-3 py-1 text-sm">
      <span>{label}</span>
      <input className="h-4 w-4 accent-slate-950" type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
    </label>
  );
}
