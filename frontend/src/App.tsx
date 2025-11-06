import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ChatInterface } from "./components/ChatInterface";
import { TaskList } from "./components/TaskList";
import { ReviewPanel } from "./components/ReviewPanel";
import KnowledgeBase from "./components/KnowledgeBase";
import TeamDirectory from "./components/TeamDirectory";
import {
  MessageSquare,
  ListTodo,
  ClipboardCheck,
  Database,
  Users,
} from "lucide-react";
import "./App.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

type Tab = "chat" | "tasks" | "review" | "knowledge" | "team";

function App() {
  const [activeTab, setActiveTab] = useState<Tab>("chat");

  return (
    <QueryClientProvider client={queryClient}>
      <div className="app-container">
        {/* Retro Brutalist Header */}
        <header className="header-main">
          <div className="header-inner">
            {/* Logo */}
            <a href="/" className="logo">
              <div className="logo-icon">TA</div>
              <span>TASK.AI</span>
            </a>

            {/* Navigation - Bold tabs */}
            <nav>
              <ul className="nav-tabs">
                {[
                  { id: "chat", label: "Submit", icon: MessageSquare },
                  { id: "tasks", label: "Overview", icon: ListTodo },
                  { id: "review", label: "Review", icon: ClipboardCheck },
                  { id: "team", label: "Team", icon: Users },
                  { id: "knowledge", label: "Knowledge", icon: Database },
                ].map((tab) => (
                  <li key={tab.id} className="nav-tab">
                    <button
                      onClick={() => setActiveTab(tab.id as Tab)}
                      className={`nav-tab-link ${
                        activeTab === tab.id ? "active" : ""
                      }`}
                    >
                      {tab.label}
                    </button>
                  </li>
                ))}
              </ul>
            </nav>

            {/* Status indicator */}
            <div className="status-indicator">
              <div className="status-led"></div>
              <span className="status-text">Online</span>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="main-content">
          <div className="content-animate">
            {activeTab === "chat" && <ChatInterface />}
            {activeTab === "tasks" && <TaskList />}
            {activeTab === "review" && <ReviewPanel />}
            {activeTab === "team" && <TeamDirectory />}
            {activeTab === "knowledge" && <KnowledgeBase />}
          </div>
        </main>

        {/* Scanline effect overlay */}
        <div className="scanline-overlay"></div>
      </div>
    </QueryClientProvider>
  );
}

export default App;
