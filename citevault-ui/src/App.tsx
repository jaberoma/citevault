import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { getHealth } from "./api/client";
import EvidenceLibrary from "./pages/admin/EvidenceLibrary";
import SourceInspector from "./pages/admin/SourceInspector";
import Settings from "./pages/admin/Settings";
import NewTailoring from "./pages/tailor/NewTailoring";
import TailoringView from "./pages/tailor/TailoringView";
import History from "./pages/tailor/History";

const qc = new QueryClient();

function Shell({ children }: { children: React.ReactNode }) {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: (query) => query.state.data?.status === "ok" ? false : 2000,
    retry: false,
  });
  const warming = !health.data || health.data.status === "loading";

  return (
    <div className="min-h-screen">
      {warming && (
        <div className="flex items-center justify-center gap-2 bg-amber-50 border-b border-amber-200 px-4 py-2 text-sm text-amber-800">
          <svg className="animate-spin h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          Backend warming up — models loading, this takes about a minute on first boot.
        </div>
      )}
      <header className="bg-white border-b border-neutral-200">
        <nav className="max-w-6xl mx-auto px-6 py-3 flex items-center gap-4">
          <span className="font-semibold tracking-tight">Citevault</span>
          <NavLink to="/admin" className={({ isActive }) =>
            `px-3 py-1 rounded ${isActive ? "bg-neutral-900 text-white" : "text-neutral-600"}`
          } end>Admin</NavLink>
          <NavLink to="/tailor" className={({ isActive }) =>
            `px-3 py-1 rounded ${isActive ? "bg-neutral-900 text-white" : "text-neutral-600"}`
          } end>New Tailor</NavLink>
          <NavLink to="/history" className={({ isActive }) =>
            `px-3 py-1 rounded ${isActive ? "bg-neutral-900 text-white" : "text-neutral-600"}`
          }>History</NavLink>
          <NavLink to="/admin/settings" className={({ isActive }) =>
            `px-3 py-1 rounded ${isActive ? "bg-neutral-900 text-white" : "text-neutral-600"}`
          }>Settings</NavLink>
        </nav>
      </header>
      <main className="max-w-6xl mx-auto px-6 py-8">{children}</main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Shell>
          <Routes>
            <Route path="/" element={<History />} />
            <Route path="/admin" element={<EvidenceLibrary />} />
            <Route path="/admin/source/:id" element={<SourceInspector />} />
            <Route path="/admin/settings" element={<Settings />} />
            <Route path="/tailor" element={<NewTailoring />} />
            <Route path="/tailor/:id" element={<TailoringView />} />
            <Route path="/history" element={<History />} />
          </Routes>
        </Shell>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
