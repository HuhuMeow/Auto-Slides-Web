import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { NewJobPanel } from "../jobs/NewJobPanel";

export function AppLayout() {
  return (
    <div className="flex min-h-screen bg-[#f7f7f8] text-slate-950">
      <Sidebar />
      <main className="min-w-0 flex-1">
        <Outlet />
      </main>
      <NewJobPanel />
    </div>
  );
}
