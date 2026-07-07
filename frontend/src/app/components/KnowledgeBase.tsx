import { BookOpen, Search, Database, FileText, Clock, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const stats = [
  { label: 'Total Documents', value: '12,458', icon: FileText, color: 'text-blue-400' },
  { label: 'Embeddings Generated', value: '45,234', icon: Database, color: 'text-purple-400' },
  { label: 'Vector Dimensions', value: '1536', icon: TrendingUp, color: 'text-green-400' },
  { label: 'Last Indexed', value: '2h ago', icon: Clock, color: 'text-yellow-400' },
];

const documents = [
  { name: 'API Documentation', type: 'Documentation', chunks: 234, size: '2.3 MB', indexed: '2 hours ago' },
  { name: 'Architecture Guide', type: 'Documentation', chunks: 156, size: '1.8 MB', indexed: '1 day ago' },
  { name: 'Code Comments', type: 'Source Code', chunks: 1243, size: '5.4 MB', indexed: '2 hours ago' },
  { name: 'README Files', type: 'Documentation', chunks: 89, size: '456 KB', indexed: '2 hours ago' },
  { name: 'Test Cases', type: 'Source Code', chunks: 567, size: '3.2 MB', indexed: '1 day ago' },
  { name: 'Database Schema', type: 'Documentation', chunks: 45, size: '234 KB', indexed: '3 days ago' },
];

const recentIndexing = [
  { document: 'src/services/payment.ts', status: 'success', chunks: 23, time: '5 min ago' },
  { document: 'docs/api/authentication.md', status: 'success', chunks: 45, time: '15 min ago' },
  { document: 'src/components/Dashboard.tsx', status: 'success', chunks: 34, time: '1 hour ago' },
  { document: 'README.md', status: 'success', chunks: 12, time: '2 hours ago' },
  { document: 'docs/architecture/overview.md', status: 'failed', chunks: 0, time: '3 hours ago' },
];

const embeddingData = [
  { model: 'OpenAI Ada-002', count: 25000 },
  { model: 'Cohere Embed', count: 12000 },
  { model: 'HuggingFace', count: 8234 },
];

export function KnowledgeBase() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Knowledge Base</h1>
          <p className="text-[#9CA3AF]">Vector database and RAG management</p>
        </div>
        <button className="px-6 py-3 bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] text-white rounded-lg hover:shadow-lg transition-all">
          Reindex All
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
            <div className="flex items-start justify-between mb-4">
              <stat.icon className={`w-8 h-8 ${stat.color}`} />
            </div>
            <div className="text-3xl font-bold text-white mb-1">{stat.value}</div>
            <div className="text-sm text-[#9CA3AF]">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Search Interface */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Search className="w-5 h-5 text-[#3B82F6]" />
          <h3 className="font-semibold text-white">Semantic Search</h3>
        </div>
        <div className="relative mb-4">
          <input
            type="text"
            placeholder="Search across all indexed documents..."
            className="w-full px-4 py-3 bg-[#111827] border border-[#374151] rounded-lg text-white placeholder-[#6B7280] focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6]"
          />
          <button className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] text-white rounded-lg hover:shadow-lg transition-all">
            Search
          </button>
        </div>
        <div className="flex gap-2">
          {['Code Examples', 'API Docs', 'Architecture', 'Database Schema'].map((filter) => (
            <button
              key={filter}
              className="text-xs px-3 py-1.5 bg-[#111827] border border-[#374151] rounded-lg text-[#9CA3AF] hover:text-white hover:border-[#3B82F6] transition-all"
            >
              {filter}
            </button>
          ))}
        </div>
      </div>

      {/* Embeddings Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Embeddings by Model</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={embeddingData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="model" 
                stroke="#9CA3AF" 
                style={{ fontSize: '12px' }}
                angle={-15}
                textAnchor="end"
                height={80}
              />
              <YAxis stroke="#9CA3AF" style={{ fontSize: '12px' }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }}
                labelStyle={{ color: '#FFFFFF' }}
              />
              <Bar dataKey="count" fill="#3B82F6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Vector Database Info */}
        <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Database className="w-5 h-5 text-[#3B82F6]" />
            <h3 className="font-semibold text-white">Vector Database</h3>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-[#111827] rounded-lg">
              <span className="text-sm text-[#9CA3AF]">Provider</span>
              <span className="text-sm font-medium text-white">Pinecone</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-[#111827] rounded-lg">
              <span className="text-sm text-[#9CA3AF]">Index Name</span>
              <span className="text-sm font-medium text-white">codepilot-main</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-[#111827] rounded-lg">
              <span className="text-sm text-[#9CA3AF]">Dimensions</span>
              <span className="text-sm font-medium text-white">1536</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-[#111827] rounded-lg">
              <span className="text-sm text-[#9CA3AF]">Metric</span>
              <span className="text-sm font-medium text-white">Cosine Similarity</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-[#111827] rounded-lg">
              <span className="text-sm text-[#9CA3AF]">Status</span>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-sm font-medium text-green-400">Connected</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Indexed Documents */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl overflow-hidden">
        <div className="p-6 border-b border-[#374151]">
          <h3 className="text-lg font-semibold text-white">Indexed Documents</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#374151]">
                <th className="text-left px-6 py-4 text-sm font-semibold text-[#9CA3AF]">Document</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-[#9CA3AF]">Type</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-[#9CA3AF]">Chunks</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-[#9CA3AF]">Size</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-[#9CA3AF]">Last Indexed</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc, index) => (
                <tr key={index} className="border-b border-[#374151] last:border-0 hover:bg-[#374151]/50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-[#3B82F6]" />
                      <span className="font-medium text-white">{doc.name}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-xs font-medium text-[#8B5CF6] bg-[#8B5CF6]/10 px-2 py-1 rounded">
                      {doc.type}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-[#9CA3AF]">{doc.chunks}</td>
                  <td className="px-6 py-4 text-sm text-[#9CA3AF]">{doc.size}</td>
                  <td className="px-6 py-4 text-sm text-[#9CA3AF]">{doc.indexed}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Indexing Activity */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Indexing Activity</h3>
        <div className="space-y-3">
          {recentIndexing.map((activity, index) => (
            <div key={index} className="flex items-center gap-4 p-4 bg-[#111827] rounded-lg">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                activity.status === 'success' ? 'bg-green-500/10' : 'bg-red-500/10'
              }`}>
                {activity.status === 'success' ? (
                  <Database className="w-4 h-4 text-green-400" />
                ) : (
                  <Database className="w-4 h-4 text-red-400" />
                )}
              </div>
              <div className="flex-1">
                <p className="text-sm text-white">{activity.document}</p>
                <p className="text-xs text-[#9CA3AF]">{activity.chunks} chunks • {activity.time}</p>
              </div>
              <span className={`text-xs font-medium px-2 py-1 rounded ${
                activity.status === 'success'
                  ? 'bg-green-500/10 text-green-400'
                  : 'bg-red-500/10 text-red-400'
              }`}>
                {activity.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
