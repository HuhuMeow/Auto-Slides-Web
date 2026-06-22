import type {
  ConversionConfig,
  Job,
  PresentationPlan,
  SpeechScript,
  ThemeOption,
  User,
  VerificationReport,
} from "./types";
import { DEFAULT_CONFIG } from "./types";

export const MOCK_USERS = [
  { id: "u_admin", username: "admin", password: "admin123", role: "admin" },
  { id: "u_user1", username: "user1", password: "user123", role: "user" },
] as const;

export const THEME_OPTIONS: ThemeOption[] = [
  "Madrid",
  "Berlin",
  "Boadilla",
  "CambridgeUS",
  "Copenhagen",
  "Darmstadt",
  "Dresden",
  "Frankfurt",
  "Ilmenau",
  "Pittsburgh",
  "Rochester",
  "Singapore",
  "Warsaw",
].map((name) => ({ name, previewUrl: `/static/themes/${name}.png` }));

export const MOCK_TEX = String.raw`\documentclass{beamer}
\usetheme{Madrid}
\title{Auto-Slides}
\subtitle{Interactive Multi-Agent Research Presentation Generation}
\author{Yuheng Yang et al.}
\date{\today}

\begin{document}

\begin{frame}
  \titlepage
\end{frame}

\begin{frame}{Problem and Motivation}
  \begin{itemize}
    \item LLM chat can answer local questions but often lacks a global learning structure.
    \item Research papers require narrative support, visual grounding, and faithful coverage.
    \item Auto-Slides turns scholarly writing into presentation-oriented learning material.
  \end{itemize}
\end{frame}

\begin{frame}{Multi-Agent Pipeline}
  \begin{itemize}
    \item Parser Agent extracts structured Markdown, figures, tables, and equations.
    \item Planner Agent reorganizes content into a PMRC narrative.
    \item Verification and Adjustment Agents improve coverage and factual fidelity.
    \item Generator and Editor Agents produce and refine Beamer slides.
  \end{itemize}
\end{frame}

\begin{frame}{Evaluation Summary}
  \begin{itemize}
    \item Learners preferred slides for visual clarity and structural organization.
    \item Interactive refinement improved perceived learning control and agency.
    \item Narrative optimization improved expert-rated flow and content accuracy.
  \end{itemize}
\end{frame}

\end{document}
`;

export const PRESENTATION_PLAN: PresentationPlan = {
  paperInfo: {
    title: "Auto-Slides: An Interactive Multi-Agent System for Creating and Customizing Research Presentations",
    authors: ["Yuheng Yang", "Wenjia Jiang", "Yang Wang", "Yi Song", "Yiwei Wang", "Chi Zhang"],
    affiliations: ["AGI Lab, Westlake University", "Teeni AI", "University of California at Merced"],
    abstract:
      "Auto-Slides converts research papers into pedagogically structured, multimodal slides and supports iterative refinement through an interactive editor.",
    keywords: ["Computing education", "Human-computer interaction", "Information visualization"],
  },
  keyContent: {
    mainContributions: [
      "A multi-agent framework for transforming academic papers into structured slide decks.",
      "Interactive customization for personalized learning.",
      "Verification and adjustment mechanisms for content completeness and accuracy.",
    ],
    methodology:
      "The system coordinates Parser, Planner, Verification, Adjustment, Generator, and Editor Agents around a PMRC narrative structure.",
    results:
      "User studies show improved visual clarity, structural support, learner acceptance, and expert-rated narrative flow.",
    figures: [
      {
        id: "fig1",
        filename: "method.png",
        path: "static/figures/method.png",
        url: "/static/figures/method.png",
        caption: "Overview of the Auto-Slides multi-agent pipeline.",
      },
    ],
    conclusions:
      "Auto-Slides bridges scholarly writing and teaching materials through structured slide generation and human-in-the-loop refinement.",
  },
  slidesPlan: [
    {
      slideNumber: 1,
      title: "Auto-Slides Overview",
      slideType: "title",
      content: [
        "Interactive multi-agent system for research presentations",
        "Transforms academic papers into structured Beamer slides",
      ],
      includesFigure: false,
      figureReference: null,
      estimatedTime: "1 minute",
    },
    {
      slideNumber: 2,
      title: "Problem and Motivation",
      slideType: "content",
      content: [
        "LLM chat can answer questions but often lacks global structure.",
        "Research papers require multimodal and narrative support for learning.",
        "Slides provide visual clarity and organized learning flow.",
      ],
      includesFigure: false,
      figureReference: null,
      estimatedTime: "2 minutes",
    },
    {
      slideNumber: 3,
      title: "Multi-Agent Pipeline",
      slideType: "figure",
      content: [
        "Parser and Planner Agents structure the paper.",
        "Verification and Adjustment Agents improve content fidelity.",
        "Generator and Editor Agents produce and refine slides.",
      ],
      includesFigure: true,
      figureReference: {
        id: "fig1",
        filename: "method.png",
        url: "/static/figures/method.png",
        caption: "Overview of the Auto-Slides multi-agent pipeline.",
      },
      estimatedTime: "3 minutes",
    },
    {
      slideNumber: 4,
      title: "User Study Findings",
      slideType: "summary",
      content: [
        "Slides outperform chat for visual clarity and structural organization.",
        "Interactive editing increases learner control and agency.",
        "Narrative optimization improves expert-rated flow.",
      ],
      includesFigure: false,
      figureReference: null,
      estimatedTime: "2 minutes",
    },
  ],
  language: "en",
  pdfPath: "uploads/autoslides.pdf",
};

export const VERIFICATION_REPORT: VerificationReport = {
  passed: false,
  coverageScore: 86,
  summary:
    "The plan covers the core system pipeline and evaluation results. One high-importance motivation detail can be strengthened before final generation.",
  missingContent: [
    {
      area: "Motivation",
      importance: "high",
      missingContent:
        "The limitation of piecemeal LLM dialogue is mentioned, but the cognitive-load motivation could be more explicit.",
      suggestedAction:
        "Add one bullet explaining that presentation sequencing reduces extraneous cognitive load.",
    },
    {
      area: "Quality Assurance",
      importance: "medium",
      missingContent:
        "Verification and adjustment are covered, but hallucination prevention is not stated directly.",
      suggestedAction:
        "Clarify that the verification loop compares the plan against source paper content.",
    },
  ],
  risks: [
    {
      type: "omission",
      severity: "medium",
      message: "The role of external knowledge retrieval is only briefly covered.",
    },
    {
      type: "format",
      severity: "low",
      message: "Slide 3 may contain more bullets than ideal for a short talk.",
    },
  ],
};

export const REPAIRED_REPORT: VerificationReport = {
  passed: true,
  coverageScore: 96,
  summary:
    "High-importance omissions were repaired. The plan now gives sufficient coverage of motivation, quality assurance, and the core agent pipeline.",
  missingContent: [],
  risks: [
    {
      type: "format",
      severity: "low",
      message: "Consider reducing slide 3 to three bullets for a fast conference talk.",
    },
  ],
};

export const SPEECH_SCRIPT: SpeechScript = {
  title: "Auto-Slides Conference Talk",
  targetDurationMinutes: 15,
  style: "academic_conference",
  sections: [
    {
      slideNumber: 1,
      slideTitle: "Auto-Slides Overview",
      duration: "1:00",
      script:
        "Today I will introduce Auto-Slides, an interactive multi-agent system that converts academic papers into structured research presentations.",
      speakerNotes: ["Set expectations: generation, review, and revision."],
    },
    {
      slideNumber: 2,
      slideTitle: "Problem and Motivation",
      duration: "2:00",
      script:
        "LLM dialogue is useful for local clarification, but it often lacks a coherent global structure. Auto-Slides addresses this by turning a paper into a pedagogically organized slide deck.",
      speakerNotes: ["Emphasize the difference between chat and structured learning material."],
    },
    {
      slideNumber: 3,
      slideTitle: "Multi-Agent Pipeline",
      duration: "3:00",
      script:
        "The pipeline starts with high-fidelity parsing, then plans a PMRC narrative, verifies coverage, adjusts missing content, and finally generates Beamer slides that can be refined through natural language.",
      speakerNotes: ["Walk through the agents from left to right."],
    },
  ],
};

const baseConfig: ConversionConfig = {
  ...DEFAULT_CONFIG,
  enableSpeech: true,
};

export function seedJobs(now = new Date()): Job[] {
  const completedAt = new Date(now.getTime() - 1000 * 60 * 45).toISOString();
  const runningAt = new Date(now.getTime() - 1000 * 7).toISOString();
  return [
    {
      id: "job_completed_autoslides",
      sessionId: "1760000000",
      userId: "u_admin",
      title: "Auto-Slides paper deck",
      status: "succeeded",
      stage: "done",
      progress: 100,
      message: "Slides generated successfully",
      estimatedRemainingSeconds: null,
      createdAt: completedAt,
      updatedAt: completedAt,
      paperFileName: "autoslides.pdf",
      paperFileSize: 1979195,
      config: baseConfig,
      texContent: MOCK_TEX,
      verificationReport: VERIFICATION_REPORT,
      speechScript: SPEECH_SCRIPT,
      artifacts: completedArtifacts("1760000000", completedAt, true),
    },
    {
      id: "job_running_example",
      sessionId: "1760000001",
      userId: "u_admin",
      title: "System paper conversion",
      status: "running",
      stage: "enhancing",
      progress: 25,
      message: "Enhancing extracted content with LLM",
      estimatedRemainingSeconds: 14,
      createdAt: runningAt,
      updatedAt: runningAt,
      mockStartedAt: runningAt,
      paperFileName: "system-paper.pdf",
      paperFileSize: 2840000,
      config: { ...DEFAULT_CONFIG, theme: "Berlin" },
      texContent: MOCK_TEX,
      verificationReport: VERIFICATION_REPORT,
      speechScript: null,
      artifacts: {
        rawContent: artifact("raw_content", "json", "lightweight_content_enhanced.json", "raw", "1760000001"),
      },
    },
    {
      id: "job_user1_completed",
      sessionId: "1760000002",
      userId: "u_user1",
      title: "HCI paper slide deck",
      status: "succeeded",
      stage: "done",
      progress: 100,
      message: "Slides generated successfully",
      estimatedRemainingSeconds: null,
      createdAt: completedAt,
      updatedAt: completedAt,
      paperFileName: "hci-paper.pdf",
      paperFileSize: 1810000,
      config: { ...DEFAULT_CONFIG, theme: "Singapore" },
      texContent: MOCK_TEX,
      verificationReport: REPAIRED_REPORT,
      speechScript: null,
      artifacts: completedArtifacts("1760000002", completedAt, false),
    },
  ];
}

export function artifact(
  id: string,
  type: "json" | "tex" | "pdf" | "image" | "txt",
  name: string,
  group: string,
  sessionId: string,
  createdAt?: string,
) {
  return {
    id,
    type,
    name,
    url: `/api/sessions/${sessionId}/files/${group}/${name}`,
    createdAt,
  };
}

export function completedArtifacts(sessionId: string, createdAt: string, includeSpeech: boolean) {
  return {
    rawContent: artifact("raw_content", "json", "lightweight_content_enhanced.json", "raw", sessionId, createdAt),
    plan: artifact("presentation_plan", "json", "lightweight_presentation_plan.json", "plan", sessionId, createdAt),
    tex: artifact("tex", "tex", "output.tex", "tex", sessionId, createdAt),
    pdf: artifact("pdf", "pdf", "placeholder-slides.pdf", "pdf", sessionId, createdAt),
    verificationReport: artifact("verification_report", "json", "verification_report.json", "verification", sessionId, createdAt),
    speech: includeSpeech ? artifact("speech", "txt", "speech_script.txt", "speech", sessionId, createdAt) : undefined,
  };
}

export function publicUser(user: (typeof MOCK_USERS)[number]): User {
  return { id: user.id, username: user.username, role: user.role };
}
