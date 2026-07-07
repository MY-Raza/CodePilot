import { useState } from 'react';
import {
  MessageSquare,
  Send,
  Paperclip,
  Sparkles,
  FileCode,
  Plus,
  MoreVertical
} from 'lucide-react';

const conversations = [
  { id: 1, title: 'Authentication Implementation', timestamp: '2 hours ago', preview: 'How do I implement JWT authentication...' },
  { id: 2, title: 'Database Schema Design', timestamp: '1 day ago', preview: 'Can you help me design a schema for...' },
  { id: 3, title: 'API Optimization', timestamp: '2 days ago', preview: 'My API endpoints are slow, what can...' },
  { id: 4, title: 'React Performance', timestamp: '3 days ago', preview: 'How can I optimize my React components...' },
];

const chatMessages = [
  { 
    role: 'user', 
    content: 'How do I implement JWT authentication in my Node.js app?',
    timestamp: '10:23 AM'
  },
  { 
    role: 'assistant', 
    content: 'I\'ll help you implement JWT authentication in Node.js. Here\'s a comprehensive approach:\n\n1. Install dependencies:\n```bash\nnpm install jsonwebtoken bcrypt\n```\n\n2. Create the authentication middleware:\n```javascript\nconst jwt = require(\'jsonwebtoken\');\n\nconst authMiddleware = (req, res, next) => {\n  const token = req.header(\'Authorization\')?.replace(\'Bearer \', \'\');\n  \n  if (!token) {\n    return res.status(401).json({ error: \'No token provided\' });\n  }\n  \n  try {\n    const decoded = jwt.verify(token, process.env.JWT_SECRET);\n    req.user = decoded;\n    next();\n  } catch (error) {\n    res.status(401).json({ error: \'Invalid token\' });\n  }\n};\n```\n\nWould you like me to explain the login and registration endpoints as well?',
    timestamp: '10:24 AM',
    sources: ['auth-middleware.js', 'user-controller.js']
  },
  { 
    role: 'user', 
    content: 'Yes, please show me the login endpoint',
    timestamp: '10:25 AM'
  },
  { 
    role: 'assistant', 
    content: 'Here\'s a secure login endpoint implementation:\n\n```javascript\nconst bcrypt = require(\'bcrypt\');\nconst jwt = require(\'jsonwebtoken\');\n\napp.post(\'/api/login\', async (req, res) => {\n  const { email, password } = req.body;\n  \n  // Find user\n  const user = await User.findOne({ email });\n  if (!user) {\n    return res.status(401).json({ error: \'Invalid credentials\' });\n  }\n  \n  // Verify password\n  const isValid = await bcrypt.compare(password, user.password);\n  if (!isValid) {\n    return res.status(401).json({ error: \'Invalid credentials\' });\n  }\n  \n  // Generate token\n  const token = jwt.sign(\n    { userId: user._id, email: user.email },\n    process.env.JWT_SECRET,\n    { expiresIn: \'7d\' }\n  );\n  \n  res.json({ token, user: { id: user._id, email: user.email } });\n});\n```\n\nThis implementation includes:\n✅ Password hashing with bcrypt\n✅ JWT token generation\n✅ Proper error handling\n✅ Token expiration',
    timestamp: '10:26 AM',
    sources: ['auth-routes.js', 'user-model.js']
  },
];

const suggestedPrompts = [
  'Explain this authentication flow',
  'Review my API design',
  'Generate tests for this function',
  'Find security vulnerabilities',
  'Optimize database queries',
  'Explain error handling best practices',
];

const referencedFiles = [
  { name: 'auth-middleware.js', path: 'src/middleware/auth.js' },
  { name: 'user-controller.js', path: 'src/controllers/user.js' },
  { name: 'auth-routes.js', path: 'src/routes/auth.js' },
];

export function AIChat() {
  const [message, setMessage] = useState('');
  const [selectedConversation, setSelectedConversation] = useState(conversations[0]);

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-6">
      {/* Conversations List */}
      <div className="w-80 bg-[#1F2937] border border-[#374151] rounded-xl p-4 flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Conversations</h2>
          <button className="p-2 bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] text-white rounded-lg hover:shadow-lg transition-all">
            <Plus className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-2">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => setSelectedConversation(conv)}
              className={`w-full text-left p-3 rounded-lg transition-all ${
                selectedConversation.id === conv.id
                  ? 'bg-[#3B82F6] text-white'
                  : 'bg-[#111827] text-[#9CA3AF] hover:bg-[#374151] hover:text-white'
              }`}
            >
              <div className="flex items-start justify-between mb-1">
                <h3 className="font-medium text-sm truncate flex-1">{conv.title}</h3>
                <MoreVertical className="w-4 h-4 flex-shrink-0 ml-2" />
              </div>
              <p className="text-xs opacity-75 truncate">{conv.preview}</p>
              <p className="text-xs opacity-60 mt-1">{conv.timestamp}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex gap-6">
        {/* Main Chat */}
        <div className="flex-1 bg-[#1F2937] border border-[#374151] rounded-xl flex flex-col">
          {/* Chat Header */}
          <div className="px-6 py-4 border-b border-[#374151]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-[#3B82F6] to-[#8B5CF6] rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="font-semibold text-white">{selectedConversation.title}</h2>
                <p className="text-xs text-[#9CA3AF]">AI-powered coding assistant</p>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {chatMessages.map((msg, index) => (
              <div key={index} className="space-y-2">
                <div className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[75%] ${msg.role === 'user' ? '' : 'w-full'}`}>
                    {msg.role === 'assistant' && (
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-6 h-6 bg-gradient-to-br from-[#3B82F6] to-[#8B5CF6] rounded-full flex items-center justify-center">
                          <Sparkles className="w-3 h-3 text-white" />
                        </div>
                        <span className="text-xs font-medium text-[#9CA3AF]">CodePilot AI</span>
                        <span className="text-xs text-[#6B7280]">{msg.timestamp}</span>
                      </div>
                    )}
                    <div
                      className={`rounded-xl px-4 py-3 ${
                        msg.role === 'user'
                          ? 'bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] text-white'
                          : 'bg-[#111827] border border-[#374151] text-white'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    </div>
                    {msg.role === 'user' && (
                      <div className="flex items-center justify-end gap-2 mt-1">
                        <span className="text-xs text-[#6B7280]">{msg.timestamp}</span>
                      </div>
                    )}
                    {msg.sources && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {msg.sources.map((source, idx) => (
                          <div key={idx} className="flex items-center gap-2 px-3 py-1.5 bg-[#374151] rounded-lg">
                            <FileCode className="w-3 h-3 text-[#3B82F6]" />
                            <span className="text-xs text-[#9CA3AF]">{source}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {/* Streaming Indicator */}
            <div className="flex items-center gap-2 text-[#9CA3AF]">
              <div className="w-6 h-6 bg-gradient-to-br from-[#3B82F6] to-[#8B5CF6] rounded-full flex items-center justify-center">
                <Sparkles className="w-3 h-3 text-white" />
              </div>
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-[#3B82F6] rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-[#3B82F6] rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-[#3B82F6] rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>

          {/* Suggested Prompts */}
          <div className="px-6 py-3 border-t border-[#374151]">
            <p className="text-xs text-[#9CA3AF] mb-2">Suggested prompts:</p>
            <div className="flex flex-wrap gap-2">
              {suggestedPrompts.slice(0, 4).map((prompt, index) => (
                <button
                  key={index}
                  className="text-xs px-3 py-1.5 bg-[#111827] border border-[#374151] rounded-lg text-[#9CA3AF] hover:text-white hover:border-[#3B82F6] transition-all"
                  onClick={() => setMessage(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>

          {/* Input */}
          <div className="p-6 border-t border-[#374151]">
            <div className="relative">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ask me anything about your code..."
                rows={3}
                className="w-full px-4 py-3 pr-24 bg-[#111827] border border-[#374151] rounded-lg text-white placeholder-[#6B7280] focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6] resize-none"
              />
              <div className="absolute bottom-3 right-3 flex items-center gap-2">
                <button className="p-2 text-[#9CA3AF] hover:text-white hover:bg-[#374151] rounded-lg transition-all">
                  <Paperclip className="w-4 h-4" />
                </button>
                <button className="p-2 bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] text-white rounded-lg hover:shadow-lg transition-all">
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Referenced Files Panel */}
        <div className="w-80 bg-[#1F2937] border border-[#374151] rounded-xl p-4">
          <h3 className="text-lg font-semibold text-white mb-4">Referenced Files</h3>
          <div className="space-y-2">
            {referencedFiles.map((file, index) => (
              <div
                key={index}
                className="p-3 bg-[#111827] border border-[#374151] rounded-lg hover:border-[#3B82F6] transition-all cursor-pointer"
              >
                <div className="flex items-start gap-3">
                  <FileCode className="w-5 h-5 text-[#3B82F6] flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{file.name}</p>
                    <p className="text-xs text-[#9CA3AF] truncate">{file.path}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6">
            <h3 className="text-sm font-semibold text-white mb-3">Sources from RAG</h3>
            <div className="space-y-2">
              <div className="p-3 bg-[#111827] border border-[#374151] rounded-lg">
                <p className="text-xs text-[#9CA3AF] mb-1">Documentation</p>
                <p className="text-sm text-white">JWT Authentication Guide</p>
              </div>
              <div className="p-3 bg-[#111827] border border-[#374151] rounded-lg">
                <p className="text-xs text-[#9CA3AF] mb-1">Code Example</p>
                <p className="text-sm text-white">Express Auth Middleware</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
