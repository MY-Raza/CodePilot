import { useState } from 'react';
import { TestTube, FileCode, Download, Play, CheckCircle, XCircle } from 'lucide-react';

const files = [
  { id: 1, name: 'src/services/auth.ts', type: 'Service' },
  { id: 2, name: 'src/utils/validation.ts', type: 'Utility' },
  { id: 3, name: 'src/components/UserProfile.tsx', type: 'Component' },
];

const generatedTests = {
  unit: `import { describe, it, expect } from 'vitest';
import { AuthService } from '../services/auth';

describe('AuthService', () => {
  it('should login with valid credentials', async () => {
    const authService = new AuthService();
    const result = await authService.login('test@example.com', 'password123');
    expect(result.token).toBeDefined();
    expect(result.user.email).toBe('test@example.com');
  });

  it('should throw error with invalid credentials', async () => {
    const authService = new AuthService();
    await expect(
      authService.login('wrong@example.com', 'wrong')
    ).rejects.toThrow('Invalid credentials');
  });

  it('should logout and clear token', async () => {
    const authService = new AuthService();
    await authService.logout();
    expect(localStorage.getItem('token')).toBeNull();
  });
});`,
  integration: `import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import request from 'supertest';
import { app } from '../app';

describe('Auth Integration Tests', () => {
  beforeAll(async () => {
    // Setup test database
  });

  afterAll(async () => {
    // Cleanup test database
  });

  it('should register a new user', async () => {
    const response = await request(app)
      .post('/api/auth/register')
      .send({
        email: 'newuser@example.com',
        password: 'securePassword123'
      });
    
    expect(response.status).toBe(201);
    expect(response.body.user.email).toBe('newuser@example.com');
  });

  it('should login existing user', async () => {
    const response = await request(app)
      .post('/api/auth/login')
      .send({
        email: 'newuser@example.com',
        password: 'securePassword123'
      });
    
    expect(response.status).toBe(200);
    expect(response.body.token).toBeDefined();
  });
});`,
  api: `import { describe, it, expect } from 'vitest';
import request from 'supertest';
import { app } from '../app';

describe('API Tests', () => {
  let authToken: string;

  it('POST /api/auth/login should return token', async () => {
    const response = await request(app)
      .post('/api/auth/login')
      .send({ email: 'test@example.com', password: 'password123' });
    
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('token');
    authToken = response.body.token;
  });

  it('GET /api/user/profile should require authentication', async () => {
    const response = await request(app)
      .get('/api/user/profile')
      .set('Authorization', \`Bearer \${authToken}\`);
    
    expect(response.status).toBe(200);
    expect(response.body.user).toBeDefined();
  });

  it('GET /api/user/profile should reject without token', async () => {
    const response = await request(app)
      .get('/api/user/profile');
    
    expect(response.status).toBe(401);
  });
});`
};

export function TestGenerator() {
  const [selectedFile, setSelectedFile] = useState(files[0]);
  const [activeTab, setActiveTab] = useState<'unit' | 'integration' | 'api'>('unit');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Test Generator</h1>
        <p className="text-[#9CA3AF]">AI-powered test case generation</p>
      </div>

      {/* File Selector */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-4">
        <label className="block text-sm font-medium text-[#9CA3AF] mb-2">Select File to Test</label>
        <select 
          className="w-full max-w-md px-4 py-2 bg-[#111827] border border-[#374151] rounded-lg text-white focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6]"
          value={selectedFile.id}
          onChange={(e) => setSelectedFile(files.find(f => f.id === Number(e.target.value)) || files[0])}
        >
          {files.map(file => (
            <option key={file.id} value={file.id}>{file.name}</option>
          ))}
        </select>
      </div>

      {/* Coverage Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <TestTube className="w-8 h-8 text-[#3B82F6]" />
            <span className="text-xs font-medium text-green-400 bg-green-500/10 px-2 py-1 rounded">+12%</span>
          </div>
          <div className="text-3xl font-bold text-white mb-1">94%</div>
          <div className="text-sm text-[#9CA3AF]">Overall Coverage</div>
        </div>

        <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <CheckCircle className="w-8 h-8 text-green-400" />
          </div>
          <div className="text-3xl font-bold text-white mb-1">247</div>
          <div className="text-sm text-[#9CA3AF]">Tests Generated</div>
        </div>

        <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <Play className="w-8 h-8 text-yellow-400" />
          </div>
          <div className="text-3xl font-bold text-white mb-1">234</div>
          <div className="text-sm text-[#9CA3AF]">Tests Passing</div>
        </div>

        <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <XCircle className="w-8 h-8 text-red-400" />
          </div>
          <div className="text-3xl font-bold text-white mb-1">13</div>
          <div className="text-sm text-[#9CA3AF]">Tests Failing</div>
        </div>
      </div>

      {/* Test Types Tabs */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl overflow-hidden">
        <div className="flex border-b border-[#374151]">
          {(['unit', 'integration', 'api'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 px-6 py-4 text-sm font-medium transition-all ${
                activeTab === tab
                  ? 'bg-[#3B82F6] text-white'
                  : 'text-[#9CA3AF] hover:text-white hover:bg-[#374151]'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)} Tests
            </button>
          ))}
        </div>

        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <FileCode className="w-5 h-5 text-[#3B82F6]" />
              <h3 className="font-semibold text-white">Generated {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Tests</h3>
            </div>
            <button className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] text-white rounded-lg hover:shadow-lg transition-all">
              <Download className="w-4 h-4" />
              Export Tests
            </button>
          </div>

          <div className="bg-[#0F172A] rounded-lg p-4 font-mono text-sm overflow-x-auto max-h-[600px] overflow-y-auto">
            <pre className="text-[#9CA3AF]">{generatedTests[activeTab]}</pre>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-4">
        <button className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg hover:shadow-lg transition-all">
          <Play className="w-5 h-5" />
          Run All Tests
        </button>
        <button className="flex items-center gap-2 px-6 py-3 bg-[#1F2937] border border-[#374151] text-white rounded-lg hover:bg-[#374151] transition-all">
          Regenerate Tests
        </button>
      </div>
    </div>
  );
}
