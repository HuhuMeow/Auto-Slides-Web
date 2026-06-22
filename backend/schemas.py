from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


Role = Literal["admin", "user"]
JobStatus = Literal["draft", "queued", "running", "waiting_user_input", "succeeded", "failed", "cancelled"]
JobStage = Literal[
    "uploading",
    "extracting",
    "enhancing",
    "planning",
    "verifying",
    "repairing",
    "generating_tex",
    "compiling",
    "generating_speech",
    "done",
]
SpeechStyle = Literal["academic_conference", "classroom", "industry_presentation", "public_talk"]
ArtifactType = Literal["json", "tex", "pdf", "image", "txt"]
LlmProvider = Literal["deepseek", "openrouter"]
EventLevel = Literal["info", "warning", "error", "success"]


class UserOut(BaseModel):
    id: str
    username: str
    role: Role


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user: UserOut
    token: str


class ConversionConfig(BaseModel):
    language: Literal["zh", "en"] = "en"
    provider: LlmProvider = "deepseek"
    model: str = "deepseek-chat"
    theme: str = "Madrid"
    enableLlmEnhancement: bool = True
    enableVerification: bool = True
    enableAutoRepair: bool = True
    skipCompilation: bool = False
    enableSpeech: bool = False
    speechDuration: int = 15
    speechStyle: SpeechStyle = "academic_conference"


class ArtifactRef(BaseModel):
    id: str
    type: ArtifactType
    name: str
    url: str
    createdAt: str | None = None


class Artifacts(BaseModel):
    rawContent: ArtifactRef | None = None
    tex: ArtifactRef | None = None
    pdf: ArtifactRef | None = None
    plan: ArtifactRef | None = None
    verificationReport: ArtifactRef | None = None
    speech: ArtifactRef | None = None


class JobEvent(BaseModel):
    id: int
    agent: str
    stage: JobStage | None = None
    level: EventLevel
    message: str
    progress: int | None = None
    createdAt: str


class JobOut(BaseModel):
    id: str
    sessionId: str
    userId: str
    title: str
    status: JobStatus
    stage: JobStage | None = None
    progress: int
    message: str | None = None
    error: str | None = None
    createdAt: str
    updatedAt: str
    estimatedRemainingSeconds: int | None = None
    paperFileName: str | None = None
    paperFileSize: int | None = None
    config: ConversionConfig
    artifacts: Artifacts | None = None
    texContent: str | None = None
    compileInProgress: bool | None = None
    speechScript: dict[str, Any] | None = None
    verificationReport: dict[str, Any] | None = None
    events: list[JobEvent] = Field(default_factory=list)


class CreateJobRequest(BaseModel):
    fileName: str
    fileSize: int
    title: str | None = None
    config: ConversionConfig = Field(default_factory=ConversionConfig)


class SaveTexRequest(BaseModel):
    tex: str


class UpdateJobRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class FigureRef(BaseModel):
    id: str
    filename: str
    path: str | None = None
    caption: str | None = None
    url: str | None = None


class SlidePlan(BaseModel):
    slideNumber: int
    title: str
    slideType: str
    content: list[str]
    includesFigure: bool | None = None
    figureReference: FigureRef | None = None
    estimatedTime: str | None = None


class PresentationPlan(BaseModel):
    paperInfo: dict[str, Any]
    keyContent: dict[str, Any]
    slidesPlan: list[SlidePlan]
    language: Literal["zh", "en"] = "en"
    pdfPath: str | None = None


class VerificationMissingContent(BaseModel):
    area: str
    importance: Literal["low", "medium", "high"]
    missingContent: str
    suggestedAction: str


class VerificationRisk(BaseModel):
    type: Literal["omission", "hallucination", "weak_evidence", "format"]
    severity: Literal["low", "medium", "high"]
    message: str


class VerificationReport(BaseModel):
    passed: bool
    coverageScore: int | None = None
    summary: str
    missingContent: list[VerificationMissingContent] = Field(default_factory=list)
    risks: list[VerificationRisk] = Field(default_factory=list)


class AgentRequest(BaseModel):
    message: str


class ProposedEdit(BaseModel):
    editId: str
    summary: str
    diffPreview: str | None = None
    proposedTex: str | None = None
    requiresConfirmation: bool = True


class AgentResponse(BaseModel):
    id: str
    message: str
    analysis: str | None = None
    proposedEdit: ProposedEdit | None = None


class ThemeOption(BaseModel):
    name: str
    previewUrl: str


class ModelOption(BaseModel):
    provider: LlmProvider
    model: str
    label: str
    configured: bool = False
    default: bool = False


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorPayload


def iso_now() -> str:
    return datetime.now().isoformat()
