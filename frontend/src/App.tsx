import { Routes, Route } from "react-router-dom";
import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";
import Board from "@/routes/Board";
import Agents from "@/routes/Agents";
import Runtime from "@/routes/Runtime";
import Models from "@/routes/Models";
import Settings from "@/routes/Settings";

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-auto p-6">
          <Routes>
            <Route path="/" element={<Board />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/runtime" element={<Runtime />} />
            <Route path="/models" element={<Models />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
