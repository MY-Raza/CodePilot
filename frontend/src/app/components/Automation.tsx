import { Zap, Play, Pause, Clock, CheckCircle, XCircle, Calendar } from 'lucide-react';

const workflows = [
  {
    id: 1,
    name: 'Daily Repository Scan',
    description: 'Scan repositories for security vulnerabilities and code quality issues',
    status: 'active',
    schedule: 'Daily at 3:00 AM',
    lastRun: '2 hours ago',
    nextRun: 'in 22 hours',
    runs: 234,
    successRate: 98
  },
  {
    id: 2,
    name: 'Auto Documentation Update',
    description: 'Automatically update documentation when code changes are detected',
    status: 'active',
    schedule: 'On every commit',
    lastRun: '15 minutes ago',
    nextRun: 'On next commit',
    runs: 1432,
    successRate: 95
  },
  {
    id: 3,
    name: 'PR Review Automation',
    description: 'Automatically review pull requests and provide feedback',
    status: 'active',
    schedule: 'On PR creation',
    lastRun: '1 hour ago',
    nextRun: 'On next PR',
    runs: 89,
    successRate: 92
  },
  {
    id: 4,
    name: 'Weekly Report Generation',
    description: 'Generate and email weekly development reports',
    status: 'paused',
    schedule: 'Weekly on Monday',
    lastRun: '6 days ago',
    nextRun: 'Paused',
    runs: 52,
    successRate: 100
  },
];

const executionHistory = [
  { workflow: 'Auto Documentation Update', status: 'success', duration: '2.3s', timestamp: '15 minutes ago' },
  { workflow: 'PR Review Automation', status: 'success', duration: '5.1s', timestamp: '1 hour ago' },
  { workflow: 'Daily Repository Scan', status: 'success', duration: '45.2s', timestamp: '2 hours ago' },
  { workflow: 'Auto Documentation Update', status: 'success', duration: '1.8s', timestamp: '3 hours ago' },
  { workflow: 'PR Review Automation', status: 'failed', duration: '0.5s', timestamp: '5 hours ago' },
  { workflow: 'Auto Documentation Update', status: 'success', duration: '2.1s', timestamp: '6 hours ago' },
];

export function Automation() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Automation</h1>
          <p className="text-[#9CA3AF]">Automated workflows and scheduled tasks</p>
        </div>
        <button className="px-6 py-3 bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] text-white rounded-lg hover:shadow-lg transition-all">
          Create Workflow
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <Zap className="w-8 h-8 text-[#3B82F6]" />
          </div>
          <div className="text-3xl font-bold text-white mb-1">4</div>
          <div className="text-sm text-[#9CA3AF]">Active Workflows</div>
        </div>

        <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <Play className="w-8 h-8 text-[#22C55E]" />
          </div>
          <div className="text-3xl font-bold text-white mb-1">1,807</div>
          <div className="text-sm text-[#9CA3AF]">Total Runs</div>
        </div>

        <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <CheckCircle className="w-8 h-8 text-[#22C55E]" />
          </div>
          <div className="text-3xl font-bold text-white mb-1">96%</div>
          <div className="text-sm text-[#9CA3AF]">Success Rate</div>
        </div>

        <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <Clock className="w-8 h-8 text-[#F59E0B]" />
          </div>
          <div className="text-3xl font-bold text-white mb-1">3.2s</div>
          <div className="text-sm text-[#9CA3AF]">Avg Duration</div>
        </div>
      </div>

      {/* Workflow Cards */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Workflows</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {workflows.map((workflow) => (
            <div key={workflow.id} className="bg-[#1F2937] border border-[#374151] rounded-xl p-6 hover:border-[#4B5563] transition-all">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-3 flex-1">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    workflow.status === 'active' 
                      ? 'bg-gradient-to-br from-green-500 to-green-600' 
                      : 'bg-gradient-to-br from-gray-500 to-gray-600'
                  }`}>
                    <Zap className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-white mb-1">{workflow.name}</h3>
                    <p className="text-sm text-[#9CA3AF]">{workflow.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-medium px-2 py-1 rounded ${
                    workflow.status === 'active'
                      ? 'bg-green-500/10 text-green-400'
                      : 'bg-gray-500/10 text-gray-400'
                  }`}>
                    {workflow.status}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-[#111827] rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Calendar className="w-4 h-4 text-[#9CA3AF]" />
                    <span className="text-xs text-[#9CA3AF]">Schedule</span>
                  </div>
                  <p className="text-sm text-white">{workflow.schedule}</p>
                </div>

                <div className="bg-[#111827] rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Clock className="w-4 h-4 text-[#9CA3AF]" />
                    <span className="text-xs text-[#9CA3AF]">Last Run</span>
                  </div>
                  <p className="text-sm text-white">{workflow.lastRun}</p>
                </div>

                <div className="bg-[#111827] rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Play className="w-4 h-4 text-[#9CA3AF]" />
                    <span className="text-xs text-[#9CA3AF]">Total Runs</span>
                  </div>
                  <p className="text-sm text-white">{workflow.runs}</p>
                </div>

                <div className="bg-[#111827] rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <CheckCircle className="w-4 h-4 text-[#9CA3AF]" />
                    <span className="text-xs text-[#9CA3AF]">Success Rate</span>
                  </div>
                  <p className="text-sm text-white">{workflow.successRate}%</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {workflow.status === 'active' ? (
                  <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-[#111827] border border-[#374151] text-white rounded-lg hover:bg-[#374151] transition-all">
                    <Pause className="w-4 h-4" />
                    Pause
                  </button>
                ) : (
                  <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-[#22C55E] to-[#16A34A] text-white rounded-lg hover:shadow-lg transition-all">
                    <Play className="w-4 h-4" />
                    Resume
                  </button>
                )}
                <button className="flex-1 px-4 py-2 bg-[#111827] border border-[#374151] text-white rounded-lg hover:bg-[#374151] transition-all">
                  Configure
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Execution History */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Execution History</h3>
        <div className="space-y-3">
          {executionHistory.map((execution, index) => (
            <div key={index} className="flex items-center gap-4 p-4 bg-[#111827] rounded-lg">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                execution.status === 'success'
                  ? 'bg-green-500/10'
                  : 'bg-red-500/10'
              }`}>
                {execution.status === 'success' ? (
                  <CheckCircle className="w-5 h-5 text-green-400" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-400" />
                )}
              </div>

              <div className="flex-1">
                <h4 className="font-medium text-white">{execution.workflow}</h4>
                <div className="flex items-center gap-4 mt-1">
                  <span className="text-xs text-[#9CA3AF]">Duration: {execution.duration}</span>
                  <span className="text-xs text-[#9CA3AF]">{execution.timestamp}</span>
                </div>
              </div>

              <span className={`text-xs font-medium px-3 py-1 rounded ${
                execution.status === 'success'
                  ? 'bg-green-500/10 text-green-400'
                  : 'bg-red-500/10 text-red-400'
              }`}>
                {execution.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
