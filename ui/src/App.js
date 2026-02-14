import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "@/pages/LandingPage";
import DashboardPage from "@/pages/DashboardPage";
import DocsPage from "@/pages/DocsPage";
import { CommandPalette } from "@/components/CommandPalette";
import { Toaster } from "sonner";
import "@/App.css";

function App() {
  return (
    <div className="dark min-h-screen bg-[#050505] text-white">
      <BrowserRouter>
        <CommandPalette />
        <Toaster theme="dark" position="bottom-right" richColors />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/docs" element={<DocsPage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
