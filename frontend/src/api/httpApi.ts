import type {
  AgentResponse,
  ArtifactRef,
  AutoSlidesApi,
  CreateJobInput,
  Job,
  LoginResponse,
  ModelOption,
  PresentationPlan,
  SpeechScript,
  ThemeOption,
  User,
  VerificationReport,
} from "./types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const TOKEN_KEY = "autoslides.http.token";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = localStorage.getItem(TOKEN_KEY);
  const isFormData = init?.body instanceof FormData;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    const message =
      body?.error?.message ||
      detail?.error?.message ||
      (typeof detail === "string" ? detail : undefined) ||
      `Request failed: ${response.status}`;
    throw new Error(message);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

async function requestBlob(path: string, init?: RequestInit): Promise<Blob> {
  const token = localStorage.getItem(TOKEN_KEY);
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    const message =
      body?.error?.message ||
      detail?.error?.message ||
      (typeof detail === "string" ? detail : undefined) ||
      `Request failed: ${response.status}`;
    throw new Error(message);
  }
  return response.blob();
}

export const httpApi: AutoSlidesApi = {
  async login(username: string, password: string): Promise<LoginResponse> {
    const response = await request<LoginResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    localStorage.setItem(TOKEN_KEY, response.token);
    return response;
  },
  async register(username: string, password: string): Promise<LoginResponse> {
    const response = await request<LoginResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    localStorage.setItem(TOKEN_KEY, response.token);
    return response;
  },
  async logout(): Promise<void> {
    await request("/api/auth/logout", { method: "POST" }).catch(() => undefined);
    localStorage.removeItem(TOKEN_KEY);
  },
  async getCurrentUser(): Promise<User | null> {
    const automatic = await request<LoginResponse | null>("/api/auth/auto-login", { method: "POST" });
    if (automatic) {
      localStorage.setItem(TOKEN_KEY, automatic.token);
      return automatic.user;
    }
    return request("/api/auth/me");
  },
  listJobs(): Promise<Job[]> {
    return request("/api/jobs");
  },
  createJob(input: CreateJobInput): Promise<Job> {
    if (input.file) {
      const body = new FormData();
      body.append("pdf", input.file);
      body.append("title", input.title || input.fileName.replace(/\.pdf$/i, ""));
      body.append("config", JSON.stringify(input.config));
      return request("/api/jobs/upload", { method: "POST", body });
    }
    return request("/api/jobs", { method: "POST", body: JSON.stringify(input) });
  },
  getJob(jobId: string): Promise<Job> {
    return request(`/api/jobs/${jobId}`);
  },
  updateJobTitle(jobId: string, title: string): Promise<Job> {
    return request(`/api/jobs/${jobId}`, { method: "PATCH", body: JSON.stringify({ title }) });
  },
  startJob(jobId: string): Promise<Job> {
    return request(`/api/jobs/${jobId}/start`, { method: "POST" });
  },
  cancelJob(jobId: string): Promise<Job> {
    return request(`/api/jobs/${jobId}/cancel`, { method: "POST" });
  },
  deleteJob(jobId: string): Promise<void> {
    return request(`/api/jobs/${jobId}`, { method: "DELETE" });
  },
  retryJob(jobId: string): Promise<Job> {
    return request(`/api/jobs/${jobId}/retry`, { method: "POST" });
  },
  getPresentationPlan(jobId: string): Promise<PresentationPlan> {
    return request(`/api/jobs/${jobId}/plan`);
  },
  getArtifacts(sessionId: string): Promise<ArtifactRef[]> {
    return request(`/api/sessions/${sessionId}/artifacts`);
  },
  saveTex(jobId: string, tex: string): Promise<Job> {
    return request(`/api/jobs/${jobId}/tex`, { method: "PUT", body: JSON.stringify({ tex }) });
  },
  compileTex(jobId: string): Promise<Job> {
    return request(`/api/jobs/${jobId}/compile`, { method: "POST" });
  },
  downloadAll(jobId: string): Promise<Blob> {
    return requestBlob(`/api/jobs/${jobId}/download-all`);
  },
  repairPlan(jobId: string): Promise<Job> {
    return request(`/api/jobs/${jobId}/repair`, { method: "POST" });
  },
  sendAgentMessage(jobId: string, message: string): Promise<AgentResponse> {
    return request(`/api/jobs/${jobId}/agent`, { method: "POST", body: JSON.stringify({ message }) });
  },
  applyAgentEdit(jobId: string, editId: string): Promise<Job> {
    return request(`/api/jobs/${jobId}/agent/edits/${editId}/apply`, { method: "POST" });
  },
  listThemes(): Promise<ThemeOption[]> {
    return request("/api/themes");
  },
  listModels(): Promise<ModelOption[]> {
    return request("/api/models");
  },
  getSpeechScript(jobId: string): Promise<SpeechScript | null> {
    return request(`/api/jobs/${jobId}/speech`);
  },
  getVerificationReport(jobId: string): Promise<VerificationReport> {
    return request(`/api/jobs/${jobId}/verification`);
  },
};
