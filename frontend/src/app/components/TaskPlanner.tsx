import { useState } from 'react';
import { ListTodo, Sparkles, CheckCircle, Circle, Link as LinkIcon } from 'lucide-react';

export function TaskPlanner() {
  const [featureRequest, setFeatureRequest] = useState('Add social media authentication (Google, Facebook, Twitter)');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Task Planner</h1>
        <p className="text-[#9CA3AF]">AI-powered feature breakdown and task generation</p>
      </div>

      {/* Input */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
        <label className="block text-sm font-medium text-[#9CA3AF] mb-2">Feature Request</label>
        <textarea
          value={featureRequest}
          onChange={(e) => setFeatureRequest(e.target.value)}
          placeholder="Describe the feature you want to implement..."
          className="w-full h-24 p-4 bg-[#111827] border border-[#374151] rounded-lg text-white placeholder-[#6B7280] focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6] resize-none"
        />
        <button className="mt-4 flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] text-white rounded-lg hover:shadow-lg transition-all">
          <Sparkles className="w-5 h-5" />
          Generate Plan
        </button>
      </div>

      {/* Epic */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
            <ListTodo className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Epic</h3>
            <p className="text-xs text-[#9CA3AF]">High-level feature description</p>
          </div>
        </div>
        <div className="bg-[#111827] rounded-lg p-4">
          <h4 className="font-semibold text-white mb-2">Social Media Authentication Integration</h4>
          <p className="text-sm text-[#9CA3AF]">
            Implement OAuth 2.0 authentication for Google, Facebook, and Twitter to allow users to sign in using their social media accounts. This will improve user onboarding and reduce friction in the registration process.
          </p>
        </div>
      </div>

      {/* User Stories */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
            <Circle className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">User Stories</h3>
            <p className="text-xs text-[#9CA3AF]">Feature from user perspective</p>
          </div>
        </div>
        <div className="space-y-3">
          {[
            'As a new user, I want to sign up using my Google account so that I can quickly create an account without filling out a form',
            'As a returning user, I want to log in with my Facebook account so that I don\'t have to remember another password',
            'As a user, I want to connect my Twitter account to my existing profile so that I can share content directly to Twitter',
          ].map((story, index) => (
            <div key={index} className="bg-[#111827] rounded-lg p-4 hover:bg-[#374151] transition-all">
              <p className="text-sm text-white">{story}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Tasks */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-white">Tasks</h3>
              <p className="text-xs text-[#9CA3AF]">Implementation checklist</p>
            </div>
          </div>
          <span className="text-sm text-[#9CA3AF]">12 tasks</span>
        </div>

        <div className="space-y-2">
          {[
            { task: 'Set up OAuth providers in application settings', estimate: '2h', priority: 'High' },
            { task: 'Install and configure Passport.js with social strategies', estimate: '3h', priority: 'High' },
            { task: 'Create Google OAuth integration', estimate: '4h', priority: 'High' },
            { task: 'Create Facebook OAuth integration', estimate: '4h', priority: 'High' },
            { task: 'Create Twitter OAuth integration', estimate: '4h', priority: 'Medium' },
            { task: 'Implement user linking for existing accounts', estimate: '5h', priority: 'High' },
            { task: 'Add social login buttons to UI', estimate: '2h', priority: 'Medium' },
            { task: 'Handle OAuth callback routes', estimate: '3h', priority: 'High' },
            { task: 'Store social tokens securely', estimate: '2h', priority: 'Critical' },
            { task: 'Add error handling for OAuth failures', estimate: '3h', priority: 'Medium' },
            { task: 'Write integration tests', estimate: '4h', priority: 'Medium' },
            { task: 'Update documentation', estimate: '2h', priority: 'Low' },
          ].map((item, index) => (
            <div key={index} className="flex items-center gap-3 p-3 bg-[#111827] rounded-lg hover:bg-[#374151] transition-all group">
              <input type="checkbox" className="w-4 h-4 rounded border-[#374151] text-[#3B82F6] focus:ring-[#3B82F6]" />
              <div className="flex-1">
                <p className="text-sm text-white group-hover:text-[#3B82F6] transition-colors">{item.task}</p>
              </div>
              <span className={`text-xs font-medium px-2 py-1 rounded ${
                item.priority === 'Critical' ? 'bg-red-500/10 text-red-400' :
                item.priority === 'High' ? 'bg-orange-500/10 text-orange-400' :
                item.priority === 'Medium' ? 'bg-yellow-500/10 text-yellow-400' :
                'bg-green-500/10 text-green-400'
              }`}>
                {item.priority}
              </span>
              <span className="text-xs text-[#9CA3AF] w-12 text-right">{item.estimate}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Acceptance Criteria */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <CheckCircle className="w-5 h-5 text-[#22C55E]" />
          <h3 className="font-semibold text-white">Acceptance Criteria</h3>
        </div>
        <div className="space-y-2">
          {[
            'Users can click on Google/Facebook/Twitter buttons on login page',
            'OAuth flow completes successfully and creates/links user account',
            'User profile shows which social accounts are connected',
            'Users can disconnect social accounts from settings',
            'Error messages are clear when OAuth fails',
            'Social tokens are stored encrypted in database',
            'Users can link multiple social accounts to one profile',
          ].map((criteria, index) => (
            <div key={index} className="flex items-start gap-3 p-3 bg-[#111827] rounded-lg">
              <CheckCircle className="w-4 h-4 text-[#22C55E] flex-shrink-0 mt-0.5" />
              <p className="text-sm text-white">{criteria}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Test Cases */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <CheckCircle className="w-5 h-5 text-[#8B5CF6]" />
          <h3 className="font-semibold text-white">Test Cases</h3>
        </div>
        <div className="space-y-3">
          {[
            { title: 'New user signs up with Google', steps: ['Click "Sign in with Google"', 'Authorize application', 'Verify account created', 'Verify user logged in'] },
            { title: 'Existing user links Facebook account', steps: ['Login with email', 'Go to settings', 'Click "Connect Facebook"', 'Verify account linked'] },
            { title: 'OAuth failure handling', steps: ['Start OAuth flow', 'Deny permissions', 'Verify error message shown', 'Verify user redirected to login'] },
          ].map((testCase, index) => (
            <div key={index} className="bg-[#111827] rounded-lg p-4">
              <h4 className="font-medium text-white mb-2">{testCase.title}</h4>
              <ol className="list-decimal list-inside space-y-1">
                {testCase.steps.map((step, stepIndex) => (
                  <li key={stepIndex} className="text-sm text-[#9CA3AF]">{step}</li>
                ))}
              </ol>
            </div>
          ))}
        </div>
      </div>

      {/* Jira Integration */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <LinkIcon className="w-5 h-5 text-[#3B82F6]" />
            <h3 className="font-semibold text-white">Jira Integration</h3>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full"></div>
            <span className="text-sm text-[#9CA3AF]">Connected</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button className="flex-1 px-6 py-3 bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] text-white rounded-lg hover:shadow-lg transition-all">
            Export to Jira
          </button>
          <button className="px-6 py-3 bg-[#111827] border border-[#374151] text-white rounded-lg hover:bg-[#374151] transition-all">
            Configure
          </button>
        </div>
      </div>
    </div>
  );
}
