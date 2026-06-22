import {
  artifact,
  completedArtifacts,
  MOCK_TEX,
  MOCK_USERS,
  PRESENTATION_PLAN,
  publicUser,
  REPAIRED_REPORT,
  seedJobs,
  SPEECH_SCRIPT,
  THEME_OPTIONS,
  VERIFICATION_REPORT,
} from "./mockData";
import type {
  AgentResponse,
  ArtifactRef,
  AutoSlidesApi,
  CreateJobInput,
  Job,
  JobStage,
  LoginResponse,
  ModelOption,
  SpeechScript,
  ThemeOption,
  User,
  VerificationReport,
} from "./types";
import { sleep } from "../lib/utils";

const AUTH_KEY = "autoslides.auth";
const JOBS_KEY = "autoslides.jobs";
const AGENT_EDIT_KEY = "autoslides.agent.edits";

type StoredAuth = {
  token: string;
  user: User;
};

const stageTimeline: Array<{ stage: JobStage; progress: number; message: string; at: number }> = [
  { stage: "extracting", progress: 10, message: "Extracting Markdown, figures, and metadata", at: 0 },
  { stage: "enhancing", progress: 25, message: "Enhancing tables and equations with LLM", at: 2600 },
  { stage: "planning", progress: 40, message: "Generating PMRC presentation plan", at: 5200 },
  { stage: "verifying", progress: 55, message: "Checking coverage against source paper", at: 7800 },
  { stage: "repairing", progress: 70, message: "Repairing high-importance omissions", at: 10400 },
  { stage: "generating_tex", progress: 82, message: "Generating Beamer LaTeX", at: 13000 },
  { stage: "compiling", progress: 95, message: "Compiling PDF presentation", at: 15600 },
  { stage: "done", progress: 100, message: "Slides generated successfully", at: 18200 },
];
const stageAgents: Record<JobStage, string> = {
  uploading: "Upload Service",
  extracting: "Extraction Service",
  enhancing: "Content Enhancement Agent",
  planning: "Planning Agent",
  verifying: "Verification Agent",
  repairing: "Repair Agent",
  generating_tex: "TEX Generation Agent",
  compiling: "TEX Compiler",
  generating_speech: "Speech Agent",
  done: "Pipeline",
};
const MOCK_AVERAGE_DURATION_SECONDS = Math.ceil(stageTimeline[stageTimeline.length - 1].at / 1000);

function readAuth(): StoredAuth | null {
  const raw = localStorage.getItem(AUTH_KEY);
  return raw ? (JSON.parse(raw) as StoredAuth) : null;
}

function writeAuth(auth: StoredAuth) {
  localStorage.setItem(AUTH_KEY, JSON.stringify(auth));
}

function readJobs(): Job[] {
  const raw = localStorage.getItem(JOBS_KEY);
  if (!raw) {
    const seeded = seedJobs();
    writeJobs(seeded);
    return seeded;
  }
  return JSON.parse(raw) as Job[];
}

function writeJobs(jobs: Job[]) {
  localStorage.setItem(JOBS_KEY, JSON.stringify(jobs));
}

function getJobOrThrow(jobId: string): Job {
  const jobs = advanceRunningJobs(readJobs());
  const job = jobs.find((item) => item.id === jobId);
  if (!job) throw new Error("Job not found");
  return job;
}

function updateJob(jobId: string, updater: (_job: Job) => Job): Job {
  const jobs = advanceRunningJobs(readJobs());
  let nextJob: Job | undefined;
  const nextJobs = jobs.map((job) => {
    if (job.id !== jobId) return job;
    nextJob = updater(job);
    return nextJob;
  });
  if (!nextJob) throw new Error("Job not found");
  writeJobs(nextJobs);
  return nextJob;
}

function currentUserOrThrow(): User {
  const auth = readAuth();
  if (!auth) throw new Error("Not authenticated");
  return auth.user;
}

function advanceRunningJobs(jobs: Job[]): Job[] {
  const now = Date.now();
  let changed = false;
  const nextJobs = jobs.map((job) => {
    if (job.status !== "running" || !job.mockStartedAt) return job;
    const elapsed = now - new Date(job.mockStartedAt).getTime();
    const current = [...stageTimeline].reverse().find((stage) => elapsed >= stage.at) ?? stageTimeline[0];
    const remainingMs = Math.max(0, stageTimeline[stageTimeline.length - 1].at - elapsed);
    const estimatedRemainingSeconds = Math.max(1, Math.ceil(remainingMs / 1000));

    if (current.stage === "done") {
      changed = true;
      const updatedAt = new Date().toISOString();
      return {
        ...job,
        status: "succeeded" as const,
        stage: "done" as const,
        progress: 100,
        message: "Slides generated successfully",
        estimatedRemainingSeconds: null,
        updatedAt,
        artifacts: completedArtifacts(job.sessionId, updatedAt, job.config.enableSpeech),
        texContent: job.texContent || MOCK_TEX,
        verificationReport: job.verificationReport || VERIFICATION_REPORT,
        speechScript: job.config.enableSpeech ? SPEECH_SCRIPT : null,
        events: [
          ...(job.events ?? []),
          {
            id: Date.now(),
            agent: "Pipeline",
            stage: "done" as const,
            level: "success" as const,
            message: current.message,
            progress: 100,
            createdAt: updatedAt,
          },
        ].slice(-40),
      };
    }

    if (
      job.stage !== current.stage ||
      job.progress !== current.progress ||
      job.estimatedRemainingSeconds !== estimatedRemainingSeconds
    ) {
      changed = true;
      return {
        ...job,
        stage: current.stage,
        progress: current.progress,
        message: current.message,
        estimatedRemainingSeconds,
        updatedAt: new Date().toISOString(),
        events:
          job.stage === current.stage
            ? job.events
            : [
                ...(job.events ?? []),
                {
                  id: Date.now(),
                  agent: stageAgents[current.stage],
                  stage: current.stage,
                  level: "info" as const,
                  message: current.message,
                  progress: current.progress,
                  createdAt: new Date().toISOString(),
                },
              ].slice(-40),
        artifacts: {
          ...job.artifacts,
          rawContent:
            job.artifacts?.rawContent ??
            artifact("raw_content", "json", "lightweight_content_enhanced.json", "raw", job.sessionId),
          plan:
            current.progress >= 40
              ? (job.artifacts?.plan ??
                artifact("presentation_plan", "json", "lightweight_presentation_plan.json", "plan", job.sessionId))
              : job.artifacts?.plan,
          verificationReport:
            current.progress >= 55
              ? (job.artifacts?.verificationReport ??
                artifact("verification_report", "json", "verification_report.json", "verification", job.sessionId))
              : job.artifacts?.verificationReport,
          tex:
            current.progress >= 82 ? (job.artifacts?.tex ?? artifact("tex", "tex", "output.tex", "tex", job.sessionId)) : job.artifacts?.tex,
        },
      };
    }
    return job;
  });
  if (changed) writeJobs(nextJobs);
  return nextJobs;
}

function makeJob(input: CreateJobInput, user: User): Job {
  const now = new Date().toISOString();
  const id = `job_${Date.now()}`;
  const sessionId = `${Date.now()}`;
  return {
    id,
    sessionId,
    userId: user.id,
    title: input.title || input.fileName.replace(/\.pdf$/i, "") || "Untitled paper",
    status: "queued",
    stage: "uploading",
    progress: 0,
    message: "Queued for conversion",
    estimatedRemainingSeconds: MOCK_AVERAGE_DURATION_SECONDS,
    error: null,
    createdAt: now,
    updatedAt: now,
    paperFileName: input.fileName,
    paperFileSize: input.fileSize,
    config: input.config,
    texContent: MOCK_TEX,
    verificationReport: VERIFICATION_REPORT,
    speechScript: input.config.enableSpeech ? SPEECH_SCRIPT : null,
    artifacts: {},
  };
}

function snakeArtifacts(artifacts?: Job["artifacts"]): ArtifactRef[] {
  if (!artifacts) return [];
  return Object.values(artifacts).filter(Boolean) as ArtifactRef[];
}

function storeEdit(editId: string, patch: string) {
  const raw = localStorage.getItem(AGENT_EDIT_KEY);
  const edits = raw ? (JSON.parse(raw) as Record<string, string>) : {};
  edits[editId] = patch;
  localStorage.setItem(AGENT_EDIT_KEY, JSON.stringify(edits));
}

function readEdit(editId: string) {
  const raw = localStorage.getItem(AGENT_EDIT_KEY);
  const edits = raw ? (JSON.parse(raw) as Record<string, string>) : {};
  return edits[editId];
}

export const mockApi: AutoSlidesApi = {
  async login(username: string, password: string): Promise<LoginResponse> {
    await sleep(450);
    const found = MOCK_USERS.find((user) => user.username === username && user.password === password);
    if (!found) throw new Error("Invalid username or password");
    const user = publicUser(found);
    const token = `mock_token_${found.id}_${Date.now()}`;
    writeAuth({ user, token });
    readJobs();
    return { user, token };
  },

  async register(username: string, password: string): Promise<LoginResponse> {
    await sleep(450);
    if (username.trim().length < 3) throw new Error("Username must be at least 3 characters");
    if (password.length < 6) throw new Error("Password must be at least 6 characters");
    const user: User = { id: `u_mock_${Date.now()}`, username: username.trim(), role: "user" };
    const token = `mock_token_${user.id}_${Date.now()}`;
    writeAuth({ user, token });
    readJobs();
    return { user, token };
  },

  async logout() {
    await sleep(150);
    localStorage.removeItem(AUTH_KEY);
  },

  async getCurrentUser() {
    await sleep(120);
    return readAuth()?.user ?? null;
  },

  async listJobs() {
    await sleep(300);
    const user = currentUserOrThrow();
    const jobs = advanceRunningJobs(readJobs());
    return jobs.filter((job) => job.userId === user.id).sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  },

  async createJob(input: CreateJobInput) {
    await sleep(650);
    const user = currentUserOrThrow();
    const job = makeJob(input, user);
    writeJobs([job, ...readJobs()]);
    return job;
  },

  async getJob(jobId: string) {
    await sleep(250);
    return getJobOrThrow(jobId);
  },

  async updateJobTitle(jobId: string, title: string) {
    await sleep(250);
    const nextTitle = title.trim();
    if (!nextTitle) throw new Error("Title cannot be empty");
    return updateJob(jobId, (job) => ({
      ...job,
      title: nextTitle,
      updatedAt: new Date().toISOString(),
    }));
  },

  async startJob(jobId: string) {
    await sleep(400);
    return updateJob(jobId, (job) => ({
      ...job,
      status: "running",
      stage: "extracting",
      progress: 10,
      message: "Extracting Markdown, figures, and metadata",
      estimatedRemainingSeconds: Math.max(1, MOCK_AVERAGE_DURATION_SECONDS - 1),
      mockStartedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }));
  },

  async cancelJob(jobId: string) {
    await sleep(250);
    return updateJob(jobId, (job) => ({
      ...job,
      status: "cancelled",
      message: "Conversion cancelled",
      updatedAt: new Date().toISOString(),
    }));
  },

  async deleteJob(jobId: string) {
    await sleep(250);
    const user = currentUserOrThrow();
    const jobs = readJobs();
    const job = jobs.find((item) => item.id === jobId);
    if (!job) throw new Error("Job not found");
    if (job.userId !== user.id && user.role !== "admin") throw new Error("Forbidden");
    writeJobs(jobs.filter((item) => item.id !== jobId));
  },

  async retryJob(jobId: string) {
    await sleep(350);
    return updateJob(jobId, (job) => ({
      ...job,
      status: "running",
      stage: "extracting",
      progress: 10,
      error: null,
      message: "Retrying conversion",
      estimatedRemainingSeconds: Math.max(1, MOCK_AVERAGE_DURATION_SECONDS - 1),
      mockStartedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }));
  },

  async getPresentationPlan() {
    await sleep(220);
    return PRESENTATION_PLAN;
  },

  async getArtifacts(sessionId: string) {
    await sleep(220);
    const jobs = advanceRunningJobs(readJobs());
    const job = jobs.find((item) => item.sessionId === sessionId);
    return snakeArtifacts(job?.artifacts);
  },

  async saveTex(jobId: string, tex: string) {
    await sleep(350);
    return updateJob(jobId, (job) => ({
      ...job,
      texContent: tex,
      updatedAt: new Date().toISOString(),
      message: "TEX saved",
    }));
  },

  async compileTex(jobId: string) {
    await sleep(1200);
    return updateJob(jobId, (job) => {
      const updatedAt = new Date().toISOString();
      return {
        ...job,
        status: "succeeded",
        stage: "done" as const,
        progress: 100,
        message: "TEX compiled successfully",
        updatedAt,
        artifacts: {
          ...job.artifacts,
          tex: artifact("tex", "tex", "output.tex", "tex", job.sessionId, updatedAt),
          pdf: artifact("pdf", "pdf", "placeholder-slides.pdf", "pdf", job.sessionId, updatedAt),
        },
      };
    });
  },

  async downloadAll(jobId: string) {
    await sleep(300);
    const job = getJobOrThrow(jobId);
    const content = `Mock Auto-Slides TEX bundle for ${job.title}\n\n${job.texContent || MOCK_TEX}`;
    return new Blob([content], { type: "application/zip" });
  },

  async repairPlan(jobId: string) {
    await sleep(900);
    return updateJob(jobId, (job) => ({
      ...job,
      verificationReport: REPAIRED_REPORT,
      message: "Verification issues repaired",
      updatedAt: new Date().toISOString(),
    }));
  },

  async sendAgentMessage(jobId: string, message: string): Promise<AgentResponse> {
    await sleep(900);
    const job = getJobOrThrow(jobId);
    const editId = `edit_${Date.now()}`;
    const patch = `${job.texContent || MOCK_TEX}

% Auto-Slides Agent note:
% ${message.replace(/\n/g, " ")}
`;
    storeEdit(editId, patch);
    return {
      id: `agent_${Date.now()}`,
      message:
        "I located the relevant Beamer frame and prepared a conservative edit. Review the diff before applying it.",
      analysis:
        "The request maps to the Editor Agent primitives: locate the relevant frame, modify the bullet density, and preserve Beamer syntax.",
      proposedEdit: {
        editId,
        summary: "Append an agent note and adjust the relevant slide content in TEX.",
        proposedTex: patch,
        diffPreview: `--- output.tex
+++ output.tex
@@
 \\end{document}
+
+% Auto-Slides Agent note:
+% ${message.slice(0, 90)}
`,
        requiresConfirmation: true,
      },
    };
  },

  async applyAgentEdit(jobId: string, editId: string) {
    await sleep(500);
    const patch = readEdit(editId);
    if (!patch) throw new Error("Edit not found");
    return updateJob(jobId, (job) => ({
      ...job,
      texContent: patch,
      message: "Agent edit applied. Recompile to refresh PDF.",
      updatedAt: new Date().toISOString(),
    }));
  },

  async listThemes(): Promise<ThemeOption[]> {
    await sleep(200);
    return THEME_OPTIONS;
  },

  async listModels(): Promise<ModelOption[]> {
    await sleep(120);
    return [
      { provider: "deepseek", model: "deepseek-chat", label: "deepseek-chat", configured: true, default: true },
      { provider: "deepseek", model: "deepseek-reasoner", label: "deepseek-reasoner", configured: true, default: false },
      { provider: "openrouter", model: "openai/gpt-4o", label: "openai/gpt-4o", configured: true, default: false },
      { provider: "openrouter", model: "openai/gpt-4.1", label: "openai/gpt-4.1", configured: true, default: false },
      { provider: "openrouter", model: "openai/gpt-4.1-mini", label: "openai/gpt-4.1-mini", configured: true, default: false },
      { provider: "openrouter", model: "openai/o4-mini", label: "openai/o4-mini", configured: true, default: false },
    ];
  },

  async getSpeechScript(jobId: string): Promise<SpeechScript | null> {
    await sleep(220);
    return getJobOrThrow(jobId).speechScript ?? null;
  },

  async getVerificationReport(jobId: string): Promise<VerificationReport> {
    await sleep(220);
    return getJobOrThrow(jobId).verificationReport ?? VERIFICATION_REPORT;
  },
};

export function getMockTex(jobId: string) {
  return getJobOrThrow(jobId).texContent || MOCK_TEX;
}
