import { create } from "zustand";
import type { AgentResponse } from "../api/types";

type ProposedEdit = NonNullable<AgentResponse["proposedEdit"]>;

interface JobUiState {
  agentCollapsed: boolean;
  newJobOpen: boolean;
  proposedEdits: Record<string, ProposedEdit | undefined>;
  sidebarCollapsed: boolean;
  setAgentCollapsed: (collapsed: boolean) => void;
  setNewJobOpen: (open: boolean) => void;
  setProposedEdit: (jobId: string, edit: ProposedEdit | null) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

export const useJobStore = create<JobUiState>((set) => ({
  agentCollapsed: false,
  newJobOpen: false,
  proposedEdits: {},
  sidebarCollapsed: false,
  setAgentCollapsed: (collapsed) => set({ agentCollapsed: collapsed }),
  setNewJobOpen: (open) => set({ newJobOpen: open }),
  setProposedEdit: (jobId, edit) =>
    set((state) => ({
      proposedEdits: {
        ...state.proposedEdits,
        [jobId]: edit ?? undefined,
      },
    })),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
}));
