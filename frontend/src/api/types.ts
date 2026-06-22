export type Role = "admin" | "user";

export interface User {
  id: string;
  username: string;
  role: Role;
}

export interface LoginResponse {
  user: User;
  token: string;
}

export type JobStatus =
  | "draft"
  | "queued"
  | "running"
  | "waiting_user_input"
  | "succeeded"
  | "failed"
  | "cancelled";

export type JobStage =
  | "uploading"
  | "extracting"
  | "enhancing"
  | "planning"
  | "verifying"
  | "repairing"
  | "generating_tex"
  | "compiling"
  | "generating_speech"
  | "done";

export type SpeechStyle =
  | "academic_conference"
  | "classroom"
  | "industry_presentation"
  | "public_talk";

export type LlmProvider = "deepseek" | "openrouter";

export interface ConversionConfig {
  language: "zh" | "en";
  provider: LlmProvider;
  model: string;
  theme: string;
  enableLlmEnhancement: boolean;
  enableVerification: boolean;
  enableAutoRepair: boolean;
  skipCompilation: boolean;
  enableSpeech: boolean;
  speechDuration: number;
  speechStyle: SpeechStyle;
}

export interface ArtifactRef {
  id: string;
  type: "json" | "tex" | "pdf" | "image" | "txt";
  name: string;
  url: string;
  createdAt?: string;
}

export interface Artifacts {
  rawContent?: ArtifactRef;
  tex?: ArtifactRef;
  pdf?: ArtifactRef;
  plan?: ArtifactRef;
  verificationReport?: ArtifactRef;
  speech?: ArtifactRef;
}

export interface JobEvent {
  id: number;
  agent: string;
  stage?: JobStage;
  level: "info" | "warning" | "error" | "success";
  message: string;
  progress?: number;
  createdAt: string;
}

export interface Job {
  id: string;
  sessionId: string;
  userId: string;
  title: string;
  status: JobStatus;
  stage?: JobStage;
  progress: number;
  message?: string;
  error?: string | null;
  createdAt: string;
  updatedAt: string;
  estimatedRemainingSeconds?: number | null;
  paperFileName?: string;
  paperFileSize?: number;
  config: ConversionConfig;
  artifacts?: Artifacts;
  texContent?: string;
  compileInProgress?: boolean;
  mockStartedAt?: string;
  speechScript?: SpeechScript | null;
  verificationReport?: VerificationReport;
  events?: JobEvent[];
}

export interface CreateJobInput {
  file?: File;
  fileName: string;
  fileSize: number;
  title?: string;
  config: ConversionConfig;
}

export interface FigureRef {
  id: string;
  filename: string;
  path?: string;
  caption?: string;
  url?: string;
}

export interface SlidePlan {
  slideNumber: number;
  title: string;
  slideType: "title" | "content" | "figure" | "table" | "equation" | "summary" | string;
  content: string[];
  includesFigure?: boolean;
  figureReference?: FigureRef | null;
  estimatedTime?: string;
}

export interface PresentationPlan {
  paperInfo: {
    title: string;
    authors: string[];
    affiliations?: string[];
    abstract?: string;
    keywords?: string[];
  };
  keyContent: {
    mainContributions: string[];
    methodology?: string;
    results?: string;
    figures?: FigureRef[];
    conclusions?: string;
  };
  slidesPlan: SlidePlan[];
  language: "zh" | "en";
  pdfPath?: string;
}

export interface VerificationReport {
  passed: boolean;
  coverageScore?: number;
  summary: string;
  missingContent: Array<{
    area: string;
    importance: "low" | "medium" | "high";
    missingContent: string;
    suggestedAction: string;
  }>;
  risks: Array<{
    type: "omission" | "hallucination" | "weak_evidence" | "format";
    severity: "low" | "medium" | "high";
    message: string;
  }>;
}

export interface SpeechScript {
  title: string;
  targetDurationMinutes: number;
  style: SpeechStyle;
  sections: Array<{
    slideNumber: number;
    slideTitle: string;
    duration: string;
    script: string;
    speakerNotes?: string[];
  }>;
}

export interface AgentResponse {
  id: string;
  message: string;
  analysis?: string;
  proposedEdit?: {
    editId: string;
    summary: string;
    diffPreview?: string;
    proposedTex?: string;
    requiresConfirmation: boolean;
  };
}

export interface AgentMessage {
  id: string;
  role: "user" | "agent";
  content: string;
  createdAt: string;
  response?: AgentResponse;
}

export interface ThemeOption {
  name: string;
  previewUrl: string;
}

export interface ModelOption {
  provider: LlmProvider;
  model: string;
  label: string;
  configured: boolean;
  default: boolean;
}

export interface AutoSlidesApi {
  login(username: string, password: string): Promise<LoginResponse>;
  register(username: string, password: string): Promise<LoginResponse>;
  logout(): Promise<void>;
  getCurrentUser(): Promise<User | null>;
  listJobs(): Promise<Job[]>;
  createJob(input: CreateJobInput): Promise<Job>;
  getJob(jobId: string): Promise<Job>;
  updateJobTitle(jobId: string, title: string): Promise<Job>;
  startJob(jobId: string): Promise<Job>;
  cancelJob(jobId: string): Promise<Job>;
  deleteJob(jobId: string): Promise<void>;
  retryJob(jobId: string): Promise<Job>;
  getPresentationPlan(jobId: string): Promise<PresentationPlan>;
  getArtifacts(sessionId: string): Promise<ArtifactRef[]>;
  saveTex(jobId: string, tex: string): Promise<Job>;
  compileTex(jobId: string): Promise<Job>;
  downloadAll(jobId: string): Promise<Blob>;
  repairPlan(jobId: string): Promise<Job>;
  sendAgentMessage(jobId: string, message: string): Promise<AgentResponse>;
  applyAgentEdit(jobId: string, editId: string): Promise<Job>;
  listThemes(): Promise<ThemeOption[]>;
  listModels(): Promise<ModelOption[]>;
  getSpeechScript(jobId: string): Promise<SpeechScript | null>;
  getVerificationReport(jobId: string): Promise<VerificationReport>;
}

export const DEFAULT_CONFIG: ConversionConfig = {
  language: "en",
  provider: "deepseek",
  model: "deepseek-chat",
  theme: "Madrid",
  enableLlmEnhancement: true,
  enableVerification: true,
  enableAutoRepair: true,
  skipCompilation: false,
  enableSpeech: false,
  speechDuration: 15,
  speechStyle: "academic_conference",
};
