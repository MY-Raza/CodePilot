import { useState } from 'react';
import { Settings as SettingsIcon, Key, Database, Moon, Sun, Github, Link as LinkIcon, CheckCircle, XCircle } from 'lucide-react';

export function Settings() {
  const [theme, setTheme] = useState('dark');

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
        <p className="text-[#9CA3AF]">Configure your CodePilot AI instance</p>
      </div>

      {/* LLM Configuration */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-6">
          <SettingsIcon className="w-5 h-5 text-[#3B82F6]" />
          <h3 className="text-lg font-semibold text-white">LLM Configuration</h3>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[#9CA3AF] mb-2">LLM Provider</label>
            <select className="w-full px-4 py-2 bg-[#111827] border border-[#374151] rounded-lg text-white focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6]">
              <option>OpenAI</option>
              <option>Anthropic</option>
              <option>Google AI</option>
              <option>Azure OpenAI</option>
              <option>Local Model</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#9CA3AF] mb-2">Model</label>
            <select className="w-full px-4 py-2 bg-[#111827] border border-[#374151] rounded-lg text-white focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6]">
              <option>gpt-4-turbo</option>
              <option>gpt-4</option>
              <option>gpt-3.5-turbo</option>
              <option>claude-3-opus</option>
              <option>claude-3-sonnet</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#9CA3AF] mb-2">Temperature</label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                defaultValue="0.7"
                className="flex-1"
              />
              <span className="text-white font-medium w-12 text-right">0.7</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#9CA3AF] mb-2">Max Tokens</label>
            <input
              type="number"
              defaultValue="2048"
              className="w-full px-4 py-2 bg-[#111827] border border-[#374151] rounded-lg text-white focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6]"
            />
          </div>
        </div>
      </div>

      {/* Embedding Configuration */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-6">
          <Database className="w-5 h-5 text-[#8B5CF6]" />
          <h3 className="text-lg font-semibold text-white">Embedding & Vector Database</h3>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[#9CA3AF] mb-2">Embedding Model</label>
            <select className="w-full px-4 py-2 bg-[#111827] border border-[#374151] rounded-lg text-white focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6]">
              <option>OpenAI text-embedding-ada-002</option>
              <option>OpenAI text-embedding-3-small</option>
              <option>OpenAI text-embedding-3-large</option>
              <option>Cohere embed-english-v3.0</option>
              <option>HuggingFace all-MiniLM-L6-v2</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#9CA3AF] mb-2">Vector Database</label>
            <select className="w-full px-4 py-2 bg-[#111827] border border-[#374151] rounded-lg text-white focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6]">
              <option>Pinecone</option>
              <option>Weaviate</option>
              <option>Qdrant</option>
              <option>Milvus</option>
              <option>ChromaDB</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#9CA3AF] mb-2">Chunk Size</label>
            <input
              type="number"
              defaultValue="512"
              className="w-full px-4 py-2 bg-[#111827] border border-[#374151] rounded-lg text-white focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6]"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[#9CA3AF] mb-2">Chunk Overlap</label>
            <input
              type="number"
              defaultValue="50"
              className="w-full px-4 py-2 bg-[#111827] border border-[#374151] rounded-lg text-white focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6]"
            />
          </div>
        </div>
      </div>

      {/* Integrations */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-6">
          <LinkIcon className="w-5 h-5 text-[#22C55E]" />
          <h3 className="text-lg font-semibold text-white">Integrations</h3>
        </div>

        <div className="space-y-4">
          {/* GitHub */}
          <div className="flex items-center justify-between p-4 bg-[#111827] rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-gray-700 to-gray-900 rounded-lg flex items-center justify-center">
                <Github className="w-5 h-5 text-white" />
              </div>
              <div>
                <h4 className="font-medium text-white">GitHub</h4>
                <p className="text-xs text-[#9CA3AF]">Connected to @mycompany</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">Connected</span>
              </div>
              <button className="px-4 py-2 bg-[#374151] text-white rounded-lg hover:bg-[#4B5563] transition-all">
                Disconnect
              </button>
            </div>
          </div>

          {/* Jira */}
          <div className="flex items-center justify-between p-4 bg-[#111827] rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                <LinkIcon className="w-5 h-5 text-white" />
              </div>
              <div>
                <h4 className="font-medium text-white">Jira</h4>
                <p className="text-xs text-[#9CA3AF]">Connected to mycompany.atlassian.net</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">Connected</span>
              </div>
              <button className="px-4 py-2 bg-[#374151] text-white rounded-lg hover:bg-[#4B5563] transition-all">
                Disconnect
              </button>
            </div>
          </div>

          {/* Slack */}
          <div className="flex items-center justify-between p-4 bg-[#111827] rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
                <LinkIcon className="w-5 h-5 text-white" />
              </div>
              <div>
                <h4 className="font-medium text-white">Slack</h4>
                <p className="text-xs text-[#9CA3AF]">Not connected</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <XCircle className="w-4 h-4 text-[#9CA3AF]" />
                <span className="text-sm text-[#9CA3AF]">Not connected</span>
              </div>
              <button className="px-4 py-2 bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] text-white rounded-lg hover:shadow-lg transition-all">
                Connect
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* API Keys */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-6">
          <Key className="w-5 h-5 text-[#F59E0B]" />
          <h3 className="text-lg font-semibold text-white">API Keys</h3>
        </div>

        <div className="space-y-4">
          {[
            { name: 'OpenAI API Key', value: 'sk-...XYZ', status: 'valid' },
            { name: 'Pinecone API Key', value: 'pc-...ABC', status: 'valid' },
            { name: 'GitHub Token', value: 'ghp_...123', status: 'valid' },
            { name: 'Jira API Token', value: 'jira_...456', status: 'valid' },
          ].map((key, index) => (
            <div key={index} className="flex items-center gap-4 p-4 bg-[#111827] rounded-lg">
              <div className="flex-1">
                <p className="text-sm font-medium text-white mb-1">{key.name}</p>
                <p className="text-xs font-mono text-[#9CA3AF]">{key.value}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs font-medium px-2 py-1 rounded bg-green-500/10 text-green-400">
                  {key.status}
                </span>
                <button className="px-3 py-1.5 bg-[#374151] text-white text-sm rounded-lg hover:bg-[#4B5563] transition-all">
                  Update
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Theme Settings */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-6">
          {theme === 'dark' ? (
            <Moon className="w-5 h-5 text-[#3B82F6]" />
          ) : (
            <Sun className="w-5 h-5 text-[#F59E0B]" />
          )}
          <h3 className="text-lg font-semibold text-white">Appearance</h3>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[#9CA3AF] mb-2">Theme</label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setTheme('dark')}
                className={`p-4 rounded-lg border-2 transition-all ${
                  theme === 'dark'
                    ? 'border-[#3B82F6] bg-[#3B82F6]/10'
                    : 'border-[#374151] bg-[#111827] hover:border-[#4B5563]'
                }`}
              >
                <Moon className="w-6 h-6 text-white mx-auto mb-2" />
                <p className="text-sm text-white">Dark</p>
              </button>
              <button
                onClick={() => setTheme('light')}
                className={`p-4 rounded-lg border-2 transition-all ${
                  theme === 'light'
                    ? 'border-[#3B82F6] bg-[#3B82F6]/10'
                    : 'border-[#374151] bg-[#111827] hover:border-[#4B5563]'
                }`}
              >
                <Sun className="w-6 h-6 text-white mx-auto mb-2" />
                <p className="text-sm text-white">Light</p>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex items-center gap-4">
        <button className="px-8 py-3 bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] text-white rounded-lg hover:shadow-lg transition-all">
          Save Changes
        </button>
        <button className="px-8 py-3 bg-[#1F2937] border border-[#374151] text-white rounded-lg hover:bg-[#374151] transition-all">
          Cancel
        </button>
      </div>
    </div>
  );
}
