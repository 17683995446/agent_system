import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";
import { Dashboard } from "./pages/Dashboard";
import { Architecture } from "./pages/Architecture";
import { Tenants } from "./pages/Tenants";
import { Services } from "./pages/Services";
import { Evolution } from "./pages/Evolution";
import { Monitoring } from "./pages/Monitoring";
import { Settings } from "./pages/Settings";
import { TestResults } from "./pages/TestResults";
import { useAppStore } from "./store";
import { cn } from "./lib/utils";

function Layout({ children }: { children: React.ReactNode }) {
  const { sidebarOpen } = useAppStore();

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />
      <Header />
      <main
        className={cn(
          "pt-16 min-h-screen transition-all duration-300",
          sidebarOpen ? "ml-64" : "ml-20"
        )}
      >
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/architecture" element={<Architecture />} />
          <Route path="/tenants" element={<Tenants />} />
          <Route path="/services" element={<Services />} />
          <Route path="/evolution" element={<Evolution />} />
          <Route path="/monitoring" element={<Monitoring />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/test-results" element={<TestResults />} />
        </Routes>
      </Layout>
    </Router>
  );
}
