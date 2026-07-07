import {
  Database,
  FileSearch,
  TestTube,
  FileText,
  Bug,
  ListChecks,
  ArrowRight,
  TrendingUp,
  Clock,
  GitBranch,
  MessageSquare,
  Folder
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const quickActions = [
  { title: 'Analyze Repository', icon: Database, color: 'from-blue-500 to-blue-600', description: 'Deep dive into codebase' },
  { title: 'Review Pull Request', icon: FileSearch, color: 'from-purple-500 to-purple-600', description: 'AI-powered PR review' },
  { title: 'Generate Tests', icon: TestTube, color: 'from-green-500 to-green-600', description: 'Auto-generate test cases' },
  { title: 'Generate Documentation', icon: FileText, color: 'from-yellow-500 to-yellow-600', description: 'Create docs from code' },
  { title: 'Debug Error', icon: Bug, color: 'from-red-500 to-red-600', description: 'AI error analysis' },
  { title: 'Create Jira Tasks', icon: ListChecks, color: 'from-indigo-500 to-indigo-600', description: 'Generate task breakdown' },
];

const stats = [
  { label: 'Indexed Files', value: '12,458', change: '+12%', icon: Folder, color: 'text-blue-400' },
  { label: 'AI Conversations', value: '342', change: '+23%', icon: MessageSquare, color: 'text-purple-400' },
  { label: 'Pull Requests Reviewed', value: '89', change: '+8%', icon: GitBranch, color: 'text-green-400' },
  { label: 'Tests Generated', value: '1,247', change: '+34%', icon: TestTube, color: 'text-yellow-400' },
  { label: 'Documentation Pages', value: '156', change: '+18%', icon: FileText, color: 'text-pink-400' },
  { label: 'Automation Runs', value: '2,341', change: '+45%', icon: TrendingUp, color: 'text-cyan-400' },
];

const recentActivity = [
  { action: 'Generated tests for authentication module', time: '5 minutes ago', type: 'test' },
  { action: 'Reviewed PR #234: Add user profile feature', time: '23 minutes ago', type: 'review' },
  { action: 'Analyzed repository: payment-service', time: '1 hour ago', type: 'analysis' },
  { action: 'Created documentation for API endpoints', time: '2 hours ago', type: 'docs' },
  { action: 'Debugged production error in checkout flow', time: '3 hours ago', type: 'debug' },
];

const recentRepos = [
  { name: 'my-saas-app', branch: 'main', files: '1,234', language: 'TypeScript', updated: '2 hours ago' },
  { name: 'payment-service', branch: 'develop', files: '456', language: 'Python', updated: '5 hours ago' },
  { name: 'mobile-app', branch: 'feature/new-ui', files: '789', language: 'React Native', updated: '1 day ago' },
];

const conversationsData = [
  { name: 'Mon', conversations: 24 },
  { name: 'Tue', conversations: 32 },
  { name: 'Wed', conversations: 45 },
  { name: 'Thu', conversations: 38 },
  { name: 'Fri', conversations: 52 },
  { name: 'Sat', conversations: 28 },
  { name: 'Sun', conversations: 15 },
];

export function Dashboard() {
  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-[#1F2937] to-[#111827] rounded-2xl p-8 border border-[#374151]">
        <div className="max-w-4xl">
          <h1 className="text-3xl font-bold text-white mb-2">Welcome back, John! 👋</h1>
          <p className="text-[#9CA3AF] mb-6">Ready to supercharge your development workflow?</p>
          
          {/* Quick AI Prompt */}
          <div className="relative">
            <input
              type="text"
              placeholder="Ask anything about your codebase..."
              className="w-full px-6 py-4 bg-[#0F172A] border border-[#374151] rounded-xl text-white placeholder-[#6B7280] focus:outline-none focus:border-[#3B82F6] focus:ring-2 focus:ring-[#3B82F6]/20 transition-all"
            />
            <button className="absolute right-3 top-1/2 -translate-y-1/2 px-4 py-2 bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] text-white rounded-lg hover:shadow-lg hover:shadow-[#3B82F6]/20 transition-all">
              Ask AI
            </button>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {quickActions.map((action) => (
            <button
              key={action.title}
              className="group bg-[#1F2937] hover:bg-[#374151] border border-[#374151] hover:border-[#4B5563] rounded-xl p-6 transition-all duration-200 text-left"
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`w-12 h-12 bg-gradient-to-br ${action.color} rounded-lg flex items-center justify-center shadow-lg`}>
                  <action.icon className="w-6 h-6 text-white" />
                </div>
                <ArrowRight className="w-5 h-5 text-[#6B7280] group-hover:text-white group-hover:translate-x-1 transition-all" />
              </div>
              <h3 className="font-semibold text-white mb-1">{action.title}</h3>
              <p className="text-sm text-[#9CA3AF]">{action.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Statistics */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Statistics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {stats.map((stat) => (
            <div key={stat.label} className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
              <div className="flex items-start justify-between mb-4">
                <stat.icon className={`w-8 h-8 ${stat.color}`} />
                <span className="text-xs font-medium text-[#22C55E] bg-[#22C55E]/10 px-2 py-1 rounded">
                  {stat.change}
                </span>
              </div>
              <div className="text-3xl font-bold text-white mb-1">{stat.value}</div>
              <div className="text-sm text-[#9CA3AF]">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Charts and Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Conversations Chart */}
        <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">AI Conversations (This Week)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={conversationsData}>
              <defs>
                <linearGradient id="colorConversations" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9CA3AF" style={{ fontSize: '12px' }} />
              <YAxis stroke="#9CA3AF" style={{ fontSize: '12px' }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }}
                labelStyle={{ color: '#FFFFFF' }}
              />
              <Area 
                type="monotone" 
                dataKey="conversations" 
                stroke="#3B82F6" 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#colorConversations)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Recent Activity */}
        <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
          <div className="space-y-4">
            {recentActivity.map((activity, index) => (
              <div key={index} className="flex items-start gap-3 pb-4 border-b border-[#374151] last:border-0 last:pb-0">
                <div className="w-2 h-2 bg-[#3B82F6] rounded-full mt-2"></div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white">{activity.action}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <Clock className="w-3 h-3 text-[#6B7280]" />
                    <span className="text-xs text-[#9CA3AF]">{activity.time}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Repositories */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Recent Repositories</h2>
        <div className="bg-[#1F2937] border border-[#374151] rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#374151]">
                  <th className="text-left px-6 py-4 text-sm font-semibold text-[#9CA3AF]">Repository</th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-[#9CA3AF]">Branch</th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-[#9CA3AF]">Files</th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-[#9CA3AF]">Language</th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-[#9CA3AF]">Last Updated</th>
                </tr>
              </thead>
              <tbody>
                {recentRepos.map((repo, index) => (
                  <tr key={index} className="border-b border-[#374151] last:border-0 hover:bg-[#374151]/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <Folder className="w-5 h-5 text-[#3B82F6]" />
                        <span className="font-medium text-white">{repo.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <GitBranch className="w-4 h-4 text-[#9CA3AF]" />
                        <span className="text-sm text-[#9CA3AF]">{repo.branch}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-[#9CA3AF]">{repo.files}</td>
                    <td className="px-6 py-4">
                      <span className="text-xs font-medium text-[#3B82F6] bg-[#3B82F6]/10 px-2 py-1 rounded">
                        {repo.language}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-[#9CA3AF]">{repo.updated}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
