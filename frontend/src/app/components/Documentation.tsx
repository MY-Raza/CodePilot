import { useState } from 'react';
import { FileText, Eye, Code, Download, BookOpen } from 'lucide-react';

const docTypes = [
  { id: 'readme', name: 'README', icon: FileText },
  { id: 'api', name: 'API Documentation', icon: Code },
  { id: 'architecture', name: 'Architecture', icon: BookOpen },
  { id: 'database', name: 'Database Schema', icon: BookOpen },
];

const readmeContent = `# My SaaS Application

A modern, scalable SaaS platform built with React, TypeScript, and Node.js.

## Features

- 🔐 **Authentication & Authorization** - Secure JWT-based authentication
- 👤 **User Management** - Complete user profile management
- 💳 **Payment Processing** - Integrated Stripe payment handling
- 📊 **Analytics Dashboard** - Real-time metrics and insights
- 🔔 **Notifications** - Email and in-app notifications
- 🌐 **Multi-tenancy** - Support for multiple organizations

## Getting Started

### Prerequisites

- Node.js 18+ 
- PostgreSQL 14+
- Redis 6+

### Installation

\`\`\`bash
# Clone the repository
git clone https://github.com/company/my-saas-app.git

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env

# Run migrations
npm run db:migrate

# Start development server
npm run dev
\`\`\`

## Architecture

The application follows a microservices architecture with the following components:

- **API Gateway** - Entry point for all requests
- **Auth Service** - Handles authentication and authorization
- **User Service** - Manages user data and profiles
- **Payment Service** - Processes payments and subscriptions
- **Notification Service** - Sends emails and push notifications

## Tech Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS
- **Backend**: Node.js, Express, TypeScript
- **Database**: PostgreSQL, Redis
- **Infrastructure**: Docker, Kubernetes, AWS

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.`;

const apiContent = `# API Documentation

## Authentication

All API requests require authentication using a Bearer token in the Authorization header.

### Login

\`\`\`http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123"
}
\`\`\`

**Response:**
\`\`\`json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "123",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
\`\`\`

## User Endpoints

### Get User Profile

\`\`\`http
GET /api/user/profile
Authorization: Bearer {token}
\`\`\`

**Response:**
\`\`\`json
{
  "id": "123",
  "email": "user@example.com",
  "name": "John Doe",
  "createdAt": "2024-01-15T10:30:00Z"
}
\`\`\`

### Update User Profile

\`\`\`http
PUT /api/user/profile
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Jane Doe",
  "bio": "Software Engineer"
}
\`\`\`

## Payment Endpoints

### Create Subscription

\`\`\`http
POST /api/payments/subscription
Authorization: Bearer {token}
Content-Type: application/json

{
  "plan": "pro",
  "paymentMethodId": "pm_123456789"
}
\`\`\`

**Response:**
\`\`\`json
{
  "subscriptionId": "sub_123456789",
  "status": "active",
  "currentPeriodEnd": "2024-02-15T10:30:00Z"
}
\`\`\``;

export function Documentation() {
  const [selectedType, setSelectedType] = useState(docTypes[0]);
  const [mode, setMode] = useState<'preview' | 'edit'>('preview');

  const getContent = () => {
    if (selectedType.id === 'readme') return readmeContent;
    if (selectedType.id === 'api') return apiContent;
    return '# Coming Soon\n\nDocumentation for this section is being generated...';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Documentation</h1>
        <p className="text-[#9CA3AF]">AI-generated project documentation</p>
      </div>

      {/* Doc Type Selector */}
      <div className="flex items-center gap-4 overflow-x-auto">
        {docTypes.map((type) => (
          <button
            key={type.id}
            onClick={() => setSelectedType(type)}
            className={`flex items-center gap-2 px-4 py-3 rounded-xl transition-all whitespace-nowrap ${
              selectedType.id === type.id
                ? 'bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] text-white shadow-lg'
                : 'bg-[#1F2937] border border-[#374151] text-[#9CA3AF] hover:text-white hover:border-[#4B5563]'
            }`}
          >
            <type.icon className="w-5 h-5" />
            <span className="font-medium">{type.name}</span>
          </button>
        ))}
      </div>

      {/* Toolbar */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setMode('preview')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                mode === 'preview'
                  ? 'bg-[#3B82F6] text-white'
                  : 'text-[#9CA3AF] hover:text-white hover:bg-[#374151]'
              }`}
            >
              <Eye className="w-4 h-4" />
              Preview
            </button>
            <button
              onClick={() => setMode('edit')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                mode === 'edit'
                  ? 'bg-[#3B82F6] text-white'
                  : 'text-[#9CA3AF] hover:text-white hover:bg-[#374151]'
              }`}
            >
              <Code className="w-4 h-4" />
              Edit
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button className="flex items-center gap-2 px-4 py-2 bg-[#111827] border border-[#374151] text-white rounded-lg hover:bg-[#374151] transition-all">
              <Download className="w-4 h-4" />
              Export PDF
            </button>
            <button className="px-4 py-2 bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] text-white rounded-lg hover:shadow-lg transition-all">
              Regenerate
            </button>
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl overflow-hidden">
        {mode === 'edit' ? (
          <textarea
            className="w-full h-[600px] p-6 bg-[#0F172A] text-white font-mono text-sm resize-none focus:outline-none"
            defaultValue={getContent()}
          />
        ) : (
          <div className="p-6 prose prose-invert max-w-none">
            <div className="text-white space-y-4">
              {getContent().split('\n\n').map((paragraph, index) => {
                // Handle headers
                if (paragraph.startsWith('# ')) {
                  return <h1 key={index} className="text-3xl font-bold text-white mb-4">{paragraph.replace('# ', '')}</h1>;
                }
                if (paragraph.startsWith('## ')) {
                  return <h2 key={index} className="text-2xl font-bold text-white mb-3 mt-8">{paragraph.replace('## ', '')}</h2>;
                }
                if (paragraph.startsWith('### ')) {
                  return <h3 key={index} className="text-xl font-bold text-white mb-2 mt-6">{paragraph.replace('### ', '')}</h3>;
                }
                
                // Handle code blocks
                if (paragraph.startsWith('```')) {
                  const code = paragraph.replace(/```[a-z]*\n?/g, '');
                  return (
                    <pre key={index} className="bg-[#0F172A] rounded-lg p-4 overflow-x-auto my-4">
                      <code className="text-sm text-[#9CA3AF]">{code}</code>
                    </pre>
                  );
                }
                
                // Handle bullet points
                if (paragraph.startsWith('- ')) {
                  const items = paragraph.split('\n');
                  return (
                    <ul key={index} className="list-disc list-inside space-y-2 text-[#9CA3AF] my-4">
                      {items.map((item, i) => (
                        <li key={i}>{item.replace('- ', '')}</li>
                      ))}
                    </ul>
                  );
                }
                
                // Regular paragraph
                return <p key={index} className="text-[#9CA3AF] leading-relaxed">{paragraph}</p>;
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
