import { useState } from 'react';
import { GitPullRequest, AlertTriangle, AlertCircle, Info, CheckCircle, FileCode, ChevronRight } from 'lucide-react';

const pullRequests = [
  { id: 234, title: 'Add user profile feature', author: 'Alice', status: 'open', files: 8 },
  { id: 233, title: 'Fix authentication bug', author: 'Bob', status: 'open', files: 3 },
  { id: 232, title: 'Update dependencies', author: 'Charlie', status: 'merged', files: 1 },
];

const changedFiles = [
  { name: 'src/components/Profile.tsx', additions: 145, deletions: 12 },
  { name: 'src/services/user.ts', additions: 67, deletions: 23 },
  { name: 'src/styles/profile.css', additions: 89, deletions: 5 },
];

const severityCounts = [
  { level: 'Critical', count: 2, color: 'from-red-500 to-red-600', textColor: 'text-red-400', bgColor: 'bg-red-500/10' },
  { level: 'High', count: 5, color: 'from-orange-500 to-orange-600', textColor: 'text-orange-400', bgColor: 'bg-orange-500/10' },
  { level: 'Medium', count: 12, color: 'from-yellow-500 to-yellow-600', textColor: 'text-yellow-400', bgColor: 'bg-yellow-500/10' },
  { level: 'Low', count: 8, color: 'from-green-500 to-green-600', textColor: 'text-green-400', bgColor: 'bg-green-500/10' },
];

const issues = [
  {
    type: 'Security',
    severity: 'Critical',
    title: 'SQL Injection vulnerability in user query',
    file: 'src/services/user.ts:45',
    description: 'Direct string interpolation in SQL query creates injection risk',
    suggestion: 'Use parameterized queries or an ORM'
  },
  {
    type: 'Performance',
    severity: 'High',
    title: 'Inefficient database query in loop',
    file: 'src/components/Profile.tsx:89',
    description: 'N+1 query problem - fetching data inside a loop',
    suggestion: 'Use batch query or JOIN to fetch all data at once'
  },
  {
    type: 'Code Smell',
    severity: 'Medium',
    title: 'Duplicate code in validation functions',
    file: 'src/utils/validation.ts:12-34',
    description: 'Similar validation logic repeated in multiple functions',
    suggestion: 'Extract common validation logic into a shared utility'
  },
];

export function CodeReview() {
  const [selectedPR, setSelectedPR] = useState(pullRequests[0]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Code Review</h1>
        <p className="text-[#9CA3AF]">AI-powered pull request analysis</p>
      </div>

      {/* PR Selector */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-4">
        <label className="block text-sm font-medium text-[#9CA3AF] mb-2">Select Pull Request</label>
        <select 
          className="w-full max-w-md px-4 py-2 bg-[#111827] border border-[#374151] rounded-lg text-white focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6]"
          value={selectedPR.id}
          onChange={(e) => setSelectedPR(pullRequests.find(pr => pr.id === Number(e.target.value)) || pullRequests[0])}
        >
          {pullRequests.map(pr => (
            <option key={pr.id} value={pr.id}>#{pr.id} - {pr.title}</option>
          ))}
        </select>
      </div>

      {/* PR Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
          <div className="flex items-start gap-4 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
              <GitPullRequest className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-white mb-1">{selectedPR.title}</h2>
              <p className="text-sm text-[#9CA3AF]">by {selectedPR.author} • {selectedPR.files} files changed</p>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-[#111827] rounded-lg">
              <span className="text-sm text-[#9CA3AF]">Status</span>
              <span className={`text-sm font-medium px-2 py-1 rounded ${
                selectedPR.status === 'open' ? 'bg-green-500/10 text-green-400' : 'bg-purple-500/10 text-purple-400'
              }`}>
                {selectedPR.status}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-[#111827] rounded-lg">
              <span className="text-sm text-[#9CA3AF]">AI Confidence</span>
              <span className="text-sm font-medium text-white">94%</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-[#111827] rounded-lg">
              <span className="text-sm text-[#9CA3AF]">Review Time</span>
              <span className="text-sm font-medium text-white">2.3s</span>
            </div>
          </div>
        </div>

        {/* Severity Cards */}
        <div className="grid grid-cols-2 gap-4">
          {severityCounts.map((severity) => (
            <div key={severity.level} className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
              <div className={`w-10 h-10 bg-gradient-to-br ${severity.color} rounded-lg flex items-center justify-center mb-3`}>
                <AlertTriangle className="w-5 h-5 text-white" />
              </div>
              <div className="text-3xl font-bold text-white mb-1">{severity.count}</div>
              <div className="text-sm text-[#9CA3AF]">{severity.level}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Changed Files */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Changed Files</h3>
        <div className="space-y-3">
          {changedFiles.map((file, index) => (
            <div key={index} className="flex items-center justify-between p-4 bg-[#111827] rounded-lg hover:bg-[#374151] transition-colors cursor-pointer">
              <div className="flex items-center gap-3 flex-1">
                <FileCode className="w-5 h-5 text-[#3B82F6]" />
                <span className="text-sm text-white">{file.name}</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm text-green-400">+{file.additions}</span>
                <span className="text-sm text-red-400">-{file.deletions}</span>
                <ChevronRight className="w-4 h-4 text-[#9CA3AF]" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Issues */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-white">AI Review Findings</h3>
        {issues.map((issue, index) => (
          <div key={index} className="bg-[#1F2937] border border-[#374151] rounded-xl p-6 hover:border-[#4B5563] transition-all">
            <div className="flex items-start gap-4">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                issue.severity === 'Critical' ? 'bg-red-500/10' :
                issue.severity === 'High' ? 'bg-orange-500/10' :
                issue.severity === 'Medium' ? 'bg-yellow-500/10' : 'bg-green-500/10'
              }`}>
                {issue.severity === 'Critical' && <AlertCircle className="w-5 h-5 text-red-400" />}
                {issue.severity === 'High' && <AlertTriangle className="w-5 h-5 text-orange-400" />}
                {issue.severity === 'Medium' && <Info className="w-5 h-5 text-yellow-400" />}
                {issue.severity === 'Low' && <CheckCircle className="w-5 h-5 text-green-400" />}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className={`text-xs font-medium px-2 py-1 rounded ${
                    issue.severity === 'Critical' ? 'bg-red-500/10 text-red-400' :
                    issue.severity === 'High' ? 'bg-orange-500/10 text-orange-400' :
                    issue.severity === 'Medium' ? 'bg-yellow-500/10 text-yellow-400' : 'bg-green-500/10 text-green-400'
                  }`}>
                    {issue.severity}
                  </span>
                  <span className="text-xs font-medium px-2 py-1 rounded bg-blue-500/10 text-blue-400">
                    {issue.type}
                  </span>
                </div>
                <h4 className="font-semibold text-white mb-2">{issue.title}</h4>
                <p className="text-sm text-[#9CA3AF] mb-2">{issue.description}</p>
                <div className="flex items-center gap-2 mb-3">
                  <FileCode className="w-4 h-4 text-[#6B7280]" />
                  <span className="text-xs text-[#6B7280]">{issue.file}</span>
                </div>
                <div className="p-3 bg-[#111827] rounded-lg border-l-4 border-[#3B82F6]">
                  <p className="text-xs text-[#9CA3AF] mb-1">💡 Suggestion:</p>
                  <p className="text-sm text-white">{issue.suggestion}</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
