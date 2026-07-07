import { useState } from 'react';
import {
  Folder,
  ChevronRight,
  ChevronDown,
  File,
  Database,
  Code2,
  FileText,
  Send,
  Sparkles
} from 'lucide-react';

const repositories = [
  { id: 1, name: 'my-saas-app', files: 1234, language: 'TypeScript' },
  { id: 2, name: 'payment-service', files: 456, language: 'Python' },
  { id: 3, name: 'mobile-app', files: 789, language: 'React Native' },
];

const overviewStats = [
  { label: 'Total Files', value: '1,234', icon: File, color: 'from-blue-500 to-blue-600' },
  { label: 'Languages', value: '8', icon: Code2, color: 'from-purple-500 to-purple-600' },
  { label: 'APIs', value: '42', icon: Database, color: 'from-green-500 to-green-600' },
  { label: 'Database Tables', value: '28', icon: Database, color: 'from-yellow-500 to-yellow-600' },
  { label: 'Documentation Coverage', value: '78%', icon: FileText, color: 'from-pink-500 to-pink-600' },
];

const fileTree = [
  {
    name: 'src',
    type: 'folder',
    children: [
      { name: 'components', type: 'folder', children: [
        { name: 'Auth.tsx', type: 'file' },
        { name: 'Dashboard.tsx', type: 'file' },
      ]},
      { name: 'services', type: 'folder', children: [
        { name: 'api.ts', type: 'file' },
        { name: 'auth.ts', type: 'file' },
      ]},
      { name: 'App.tsx', type: 'file' },
    ],
  },
  { name: 'package.json', type: 'file' },
  { name: 'README.md', type: 'file' },
];

const suggestedQuestions = [
  'Explain the authentication flow',
  'Explain the overall architecture',
  'Find duplicate code',
  'Show me the API flow',
  'Explain the database schema',
];

const messages = [
  { role: 'user', content: 'Explain the authentication flow' },
  { 
    role: 'assistant', 
    content: 'The authentication flow in this application uses JWT tokens. Here\'s how it works:\n\n1. User submits credentials\n2. Server validates and generates JWT\n3. Token stored in localStorage\n4. Subsequent requests include token in Authorization header\n\nKey files: `src/services/auth.ts`, `src/components/Auth.tsx`' 
  },
];

function FileTreeItem({ item, depth = 0 }: { item: any; depth?: number }) {
  const [isOpen, setIsOpen] = useState(false);
  const isFolder = item.type === 'folder';

  return (
    <div>
      <div
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-[#374151] cursor-pointer transition-colors`}
        style={{ paddingLeft: `${depth * 16 + 12}px` }}
        onClick={() => isFolder && setIsOpen(!isOpen)}
      >
        {isFolder && (
          isOpen ? <ChevronDown className="w-4 h-4 text-[#9CA3AF]" /> : <ChevronRight className="w-4 h-4 text-[#9CA3AF]" />
        )}
        {!isFolder && <div className="w-4" />}
        {isFolder ? (
          <Folder className="w-4 h-4 text-[#3B82F6]" />
        ) : (
          <File className="w-4 h-4 text-[#9CA3AF]" />
        )}
        <span className="text-sm text-white">{item.name}</span>
      </div>
      {isFolder && isOpen && item.children && (
        <div>
          {item.children.map((child: any, index: number) => (
            <FileTreeItem key={index} item={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export function RepositoryIntelligence() {
  const [selectedRepo, setSelectedRepo] = useState(repositories[0]);
  const [message, setMessage] = useState('');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Repository Intelligence</h1>
        <p className="text-[#9CA3AF]">Deep insights into your codebase</p>
      </div>

      {/* Repository Selector */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-4">
        <label className="block text-sm font-medium text-[#9CA3AF] mb-2">Select Repository</label>
        <select 
          className="w-full max-w-md px-4 py-2 bg-[#111827] border border-[#374151] rounded-lg text-white focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6]"
          value={selectedRepo.id}
          onChange={(e) => setSelectedRepo(repositories.find(r => r.id === Number(e.target.value)) || repositories[0])}
        >
          {repositories.map(repo => (
            <option key={repo.id} value={repo.id}>{repo.name}</option>
          ))}
        </select>
      </div>

      {/* Overview Stats */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Repository Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {overviewStats.map((stat) => (
            <div key={stat.label} className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
              <div className={`w-10 h-10 bg-gradient-to-br ${stat.color} rounded-lg flex items-center justify-center mb-3`}>
                <stat.icon className="w-5 h-5 text-white" />
              </div>
              <div className="text-2xl font-bold text-white mb-1">{stat.value}</div>
              <div className="text-sm text-[#9CA3AF]">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* File Tree */}
        <div className="lg:col-span-1">
          <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-4 h-[600px] flex flex-col">
            <h3 className="text-lg font-semibold text-white mb-4">File Explorer</h3>
            <div className="flex-1 overflow-y-auto">
              {fileTree.map((item, index) => (
                <FileTreeItem key={index} item={item} />
              ))}
            </div>
          </div>
        </div>

        {/* Code Viewer & AI Chat */}
        <div className="lg:col-span-2 space-y-6">
          {/* Code Viewer */}
          <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">src/services/auth.ts</h3>
              <span className="text-xs font-medium text-[#3B82F6] bg-[#3B82F6]/10 px-2 py-1 rounded">TypeScript</span>
            </div>
            <div className="bg-[#0F172A] rounded-lg p-4 font-mono text-sm overflow-x-auto">
              <pre className="text-[#9CA3AF]">
{`export class AuthService {
  async login(email: string, password: string) {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    localStorage.setItem('token', data.token);
    return data;
  }
  
  async logout() {
    localStorage.removeItem('token');
  }
}`}
              </pre>
            </div>
          </div>

          {/* AI Chat Panel */}
          <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-4 h-[400px] flex flex-col">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-[#3B82F6]" />
              <h3 className="text-lg font-semibold text-white">Ask AI About This Repository</h3>
            </div>

            {/* Suggested Questions */}
            <div className="mb-4">
              <p className="text-xs text-[#9CA3AF] mb-2">Suggested Questions:</p>
              <div className="flex flex-wrap gap-2">
                {suggestedQuestions.map((question, index) => (
                  <button
                    key={index}
                    className="text-xs px-3 py-1.5 bg-[#111827] border border-[#374151] rounded-lg text-[#9CA3AF] hover:text-white hover:border-[#3B82F6] transition-all"
                    onClick={() => setMessage(question)}
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto mb-4 space-y-4">
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-xl px-4 py-3 ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] text-white'
                        : 'bg-[#111827] border border-[#374151] text-white'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Input */}
            <div className="relative">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ask about architecture, APIs, database schema..."
                className="w-full px-4 py-3 pr-12 bg-[#111827] border border-[#374151] rounded-lg text-white placeholder-[#6B7280] focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6]"
              />
              <button className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] text-white rounded-lg hover:shadow-lg transition-all">
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
