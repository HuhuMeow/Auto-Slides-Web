import { LogOut, PanelLeftClose, PanelLeftOpen, Plus, Presentation } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { useAuthStore } from "../../store/authStore";
import { useJobStore } from "../../store/jobStore";
import { JobList } from "../jobs/JobList";

export function Sidebar() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const collapsed = useJobStore((state) => state.sidebarCollapsed);
  const setNewJobOpen = useJobStore((state) => state.setNewJobOpen);
  const setSidebarCollapsed = useJobStore((state) => state.setSidebarCollapsed);
  const { data: jobs = [] } = useQuery({
    queryKey: ["jobs"],
    queryFn: api.listJobs,
    refetchInterval: 1500,
  });

  async function onLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <aside className={`${collapsed ? "w-16" : "w-80"} flex h-screen shrink-0 flex-col border-r bg-white transition-[width] duration-200`}>
      <div className={`${collapsed ? "p-3" : "p-4"} border-b`}>
        <div className={`flex items-center ${collapsed ? "justify-center" : "justify-between gap-3"}`}>
          <button className="flex min-w-0 items-center gap-2" onClick={() => navigate("/")}>
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-slate-950 text-white">
              <Presentation className="h-5 w-5" />
            </span>
            {!collapsed ? (
              <span className="min-w-0 text-left">
                <span className="block truncate text-sm font-semibold">Auto-Slides</span>
                <span className="block truncate text-xs text-slate-500">Academic deck generator</span>
              </span>
            ) : null}
          </button>
          {!collapsed ? (
            <button className="rounded-md p-2 hover:bg-muted" onClick={() => setSidebarCollapsed(true)} title="Collapse sidebar">
              <PanelLeftClose className="h-4 w-4" />
            </button>
          ) : null}
        </div>
        {collapsed ? (
          <button className="mt-3 flex h-9 w-full items-center justify-center rounded-md border hover:bg-muted" onClick={() => setSidebarCollapsed(false)} title="Expand sidebar">
            <PanelLeftOpen className="h-4 w-4" />
          </button>
        ) : null}
      </div>

      {collapsed ? (
        <>
          <div className="border-b p-3">
            <button
              className="flex h-10 w-full items-center justify-center rounded-md bg-slate-950 text-white"
              onClick={() => setNewJobOpen(true)}
              title="New task"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
          <div className="flex-1" />
          <div className="border-t p-3">
            <button className="flex h-9 w-full items-center justify-center rounded-md border hover:bg-muted" onClick={onLogout} title={`Sign out ${user?.username ?? ""}`}>
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </>
      ) : (
        <>
          <div className="border-b p-4">
            <button
              className="flex h-10 w-full items-center justify-center gap-2 rounded-md bg-slate-950 text-sm font-medium text-white"
              onClick={() => setNewJobOpen(true)}
            >
              <Plus className="h-4 w-4" />
              New task
            </button>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto p-4">
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Tasks</div>
            <JobList jobs={jobs} />
          </div>

          <div className="border-t p-4">
            <div className="mb-3 min-w-0">
              <div className="truncate text-sm font-medium">{user?.username}</div>
              <div className="text-xs text-slate-500">{user?.role}</div>
            </div>
            <button
              className="flex h-9 w-full items-center justify-center gap-2 rounded-md border bg-white text-sm hover:bg-muted"
              onClick={onLogout}
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </div>
        </>
      )}
    </aside>
  );
}
