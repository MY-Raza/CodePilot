import { Search, Bell, Moon, Sun, ChevronDown, GitBranch } from 'lucide-react';
import { useState } from 'react';

export function TopNav() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  return (
    <header className="h-16 bg-[#111827] border-b border-[#374151] flex items-center justify-between px-6">
      <div className="flex items-center gap-4 flex-1">
        {/* Workspace Selector */}
        <div className="flex items-center gap-2 px-3 py-2 bg-[#1F2937] rounded-lg border border-[#374151] hover:border-[#4B5563] transition-colors cursor-pointer">
          <span className="text-sm font-medium text-white">My Workspace</span>
          <ChevronDown className="w-4 h-4 text-[#9CA3AF]" />
        </div>

        {/* Repository Status */}
        <div className="flex items-center gap-2 px-3 py-2 bg-[#1F2937] rounded-lg border border-[#374151]">
          <GitBranch className="w-4 h-4 text-[#22C55E]" />
          <span className="text-sm text-white">main</span>
          <div className="w-1.5 h-1.5 bg-[#22C55E] rounded-full"></div>
          <span className="text-xs text-[#9CA3AF]">my-saas-app</span>
        </div>

        {/* Search Bar */}
        <div className="flex-1 max-w-lg">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" />
            <input
              type="text"
              placeholder="Search files, conversations, documentation..."
              className="w-full pl-10 pr-4 py-2 bg-[#1F2937] border border-[#374151] rounded-lg text-sm text-white placeholder-[#6B7280] focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6] transition-all"
            />
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Notifications */}
        <button className="relative p-2 text-[#9CA3AF] hover:text-white hover:bg-[#1F2937] rounded-lg transition-all">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-[#EF4444] rounded-full"></span>
        </button>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 text-[#9CA3AF] hover:text-white hover:bg-[#1F2937] rounded-lg transition-all"
        >
          {theme === 'dark' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
        </button>

        {/* User Profile */}
        <div className="flex items-center gap-2 px-3 py-2 bg-[#1F2937] rounded-lg border border-[#374151] hover:border-[#4B5563] transition-colors cursor-pointer">
          <div className="w-7 h-7 bg-gradient-to-br from-[#8B5CF6] to-[#3B82F6] rounded-full flex items-center justify-center text-xs font-bold">
            JD
          </div>
          <ChevronDown className="w-4 h-4 text-[#9CA3AF]" />
        </div>
      </div>
    </header>
  );
}
