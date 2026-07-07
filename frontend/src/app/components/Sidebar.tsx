import { NavLink } from 'react-router';
import {
  LayoutDashboard,
  Database,
  MessageSquare,
  FileSearch,
  TestTube,
  FileText,
  Bug,
  ListTodo,
  Zap,
  BookOpen,
  Settings,
  Code2
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/repository', label: 'Repository Intelligence', icon: Database },
  { path: '/chat', label: 'AI Chat', icon: MessageSquare },
  { path: '/review', label: 'Code Review', icon: FileSearch },
  { path: '/tests', label: 'Test Generator', icon: TestTube },
  { path: '/documentation', label: 'Documentation', icon: FileText },
  { path: '/debug', label: 'Debug Assistant', icon: Bug },
  { path: '/tasks', label: 'Task Planner', icon: ListTodo },
  { path: '/automation', label: 'Automation', icon: Zap },
  { path: '/knowledge', label: 'Knowledge Base', icon: BookOpen },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="w-64 bg-[#111827] border-r border-[#374151] flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-[#374151]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-[#3B82F6] to-[#8B5CF6] rounded-xl flex items-center justify-center">
            <Code2 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">CodePilot AI</h1>
            <p className="text-xs text-[#9CA3AF]">Engineering Copilot</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-3">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-[#3B82F6] text-white shadow-lg shadow-[#3B82F6]/20'
                      : 'text-[#9CA3AF] hover:bg-[#1F2937] hover:text-white'
                  }`
                }
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                <span className="text-sm font-medium">{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-[#374151]">
        <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-[#1F2937]">
          <div className="w-8 h-8 bg-gradient-to-br from-[#8B5CF6] to-[#3B82F6] rounded-full flex items-center justify-center text-xs font-bold">
            JD
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">John Doe</p>
            <p className="text-xs text-[#9CA3AF] truncate">john@company.com</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
