import { createBrowserRouter } from "react-router";
import { Layout } from "./components/Layout";
import { Dashboard } from "./components/Dashboard";
import { RepositoryIntelligence } from "./components/RepositoryIntelligence";
import { AIChat } from "./components/AIChat";
import { CodeReview } from "./components/CodeReview";
import { TestGenerator } from "./components/TestGenerator";
import { Documentation } from "./components/Documentation";
import { DebugAssistant } from "./components/DebugAssistant";
import { TaskPlanner } from "./components/TaskPlanner";
import { Automation } from "./components/Automation";
import { KnowledgeBase } from "./components/KnowledgeBase";
import { Settings } from "./components/Settings";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      { index: true, Component: Dashboard },
      { path: "repository", Component: RepositoryIntelligence },
      { path: "chat", Component: AIChat },
      { path: "review", Component: CodeReview },
      { path: "tests", Component: TestGenerator },
      { path: "documentation", Component: Documentation },
      { path: "debug", Component: DebugAssistant },
      { path: "tasks", Component: TaskPlanner },
      { path: "automation", Component: Automation },
      { path: "knowledge", Component: KnowledgeBase },
      { path: "settings", Component: Settings },
    ],
  },
]);
