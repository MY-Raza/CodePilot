import { useState } from 'react';
import { Bug, Upload, Sparkles, FileCode, AlertCircle, CheckCircle } from 'lucide-react';

const sampleError = `Error: Cannot read property 'user' of undefined
    at getUserProfile (src/controllers/user.ts:45:23)
    at Layer.handle [as handle_request] (express/lib/router/layer.js:95:5)
    at next (express/lib/router/route.js:137:13)
    at Route.dispatch (express/lib/router/route.js:112:3)
    at Layer.handle [as handle_request] (express/lib/router/layer.js:95:5)
    at express/lib/router/index.js:281:22`;

export function DebugAssistant() {
  const [stackTrace, setStackTrace] = useState(sampleError);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Debug Assistant</h1>
        <p className="text-[#9CA3AF]">AI-powered error analysis and debugging</p>
      </div>

      {/* Input Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Bug className="w-5 h-5 text-[#EF4444]" />
            <h3 className="font-semibold text-white">Stack Trace</h3>
          </div>
          <textarea
            value={stackTrace}
            onChange={(e) => setStackTrace(e.target.value)}
            placeholder="Paste your error stack trace here..."
            className="w-full h-64 p-4 bg-[#0F172A] border border-[#374151] rounded-lg text-white font-mono text-sm placeholder-[#6B7280] focus:outline-none focus:border-[#3B82F6] focus:ring-1 focus:ring-[#3B82F6] resize-none"
          />
          <div className="flex items-center gap-3 mt-4">
            <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] text-white rounded-lg hover:shadow-lg transition-all">
              <Sparkles className="w-4 h-4" />
              Analyze Error
            </button>
          </div>
        </div>

        <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Upload className="w-5 h-5 text-[#3B82F6]" />
            <h3 className="font-semibold text-white">Upload Log File</h3>
          </div>
          <div className="border-2 border-dashed border-[#374151] rounded-lg p-8 text-center hover:border-[#3B82F6] transition-all cursor-pointer">
            <Upload className="w-12 h-12 text-[#9CA3AF] mx-auto mb-3" />
            <p className="text-sm text-white mb-1">Drop your log file here</p>
            <p className="text-xs text-[#9CA3AF]">or click to browse</p>
            <button className="mt-4 px-4 py-2 bg-[#111827] border border-[#374151] text-white rounded-lg hover:bg-[#374151] transition-all">
              Select File
            </button>
          </div>
        </div>
      </div>

      {/* Analysis Results */}
      <div className="bg-[#1F2937] border border-[#374151] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-6">
          <Sparkles className="w-5 h-5 text-[#3B82F6]" />
          <h3 className="text-lg font-semibold text-white">AI Analysis</h3>
        </div>

        {/* Root Cause */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle className="w-5 h-5 text-[#F59E0B]" />
            <h4 className="font-semibold text-white">Root Cause Analysis</h4>
          </div>
          <div className="bg-[#111827] rounded-lg p-4 border-l-4 border-[#F59E0B]">
            <p className="text-white mb-2">
              The error occurs because the <code className="px-2 py-1 bg-[#374151] rounded text-[#3B82F6]">req.session</code> object is undefined when trying to access the user property.
            </p>
            <p className="text-[#9CA3AF] text-sm">
              This typically happens when:
            </p>
            <ul className="list-disc list-inside text-[#9CA3AF] text-sm mt-2 space-y-1 ml-4">
              <li>Session middleware is not properly configured</li>
              <li>Session has expired or been invalidated</li>
              <li>Request is made without proper authentication</li>
            </ul>
          </div>
        </div>

        {/* Suggested Fix */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle className="w-5 h-5 text-[#22C55E]" />
            <h4 className="font-semibold text-white">Suggested Fix</h4>
          </div>
          <div className="bg-[#0F172A] rounded-lg p-4">
            <p className="text-[#9CA3AF] text-sm mb-3">Add null checking before accessing user property:</p>
            <pre className="text-sm text-[#9CA3AF] overflow-x-auto">
{`// Before (causing error)
const getUserProfile = (req, res) => {
  const userId = req.session.user.id; // Error here
  // ...
};

// After (with fix)
const getUserProfile = (req, res) => {
  if (!req.session || !req.session.user) {
    return res.status(401).json({ 
      error: 'Unauthorized - No active session' 
    });
  }
  
  const userId = req.session.user.id;
  // ...
};`}
            </pre>
          </div>
        </div>

        {/* Patch Preview */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <FileCode className="w-5 h-5 text-[#8B5CF6]" />
            <h4 className="font-semibold text-white">Patch Preview</h4>
          </div>
          <div className="bg-[#0F172A] rounded-lg p-4">
            <div className="font-mono text-sm">
              <div className="text-[#9CA3AF] mb-1">src/controllers/user.ts</div>
              <div className="flex">
                <div className="w-12 text-right pr-4 text-[#6B7280] select-none">43</div>
                <div className="flex-1 text-[#9CA3AF]">export const getUserProfile = async (req, res) =&gt; {'{'}</div>
              </div>
              <div className="flex bg-red-500/10">
                <div className="w-12 text-right pr-4 text-[#6B7280] select-none">44</div>
                <div className="flex-1">
                  <span className="text-red-400">-  const userId = req.session.user.id;</span>
                </div>
              </div>
              <div className="flex bg-green-500/10">
                <div className="w-12 text-right pr-4 text-[#6B7280] select-none">44</div>
                <div className="flex-1">
                  <span className="text-green-400">+  if (!req.session || !req.session.user) {'{'}</span>
                </div>
              </div>
              <div className="flex bg-green-500/10">
                <div className="w-12 text-right pr-4 text-[#6B7280] select-none">45</div>
                <div className="flex-1">
                  <span className="text-green-400">+    return res.status(401).json({'{'} error: 'Unauthorized' {'}'});</span>
                </div>
              </div>
              <div className="flex bg-green-500/10">
                <div className="w-12 text-right pr-4 text-[#6B7280] select-none">46</div>
                <div className="flex-1">
                  <span className="text-green-400">+  {'}'}</span>
                </div>
              </div>
              <div className="flex bg-green-500/10">
                <div className="w-12 text-right pr-4 text-[#6B7280] select-none">47</div>
                <div className="flex-1">
                  <span className="text-green-400">+  const userId = req.session.user.id;</span>
                </div>
              </div>
              <div className="flex">
                <div className="w-12 text-right pr-4 text-[#6B7280] select-none">48</div>
                <div className="flex-1 text-[#9CA3AF]">  // Rest of function...</div>
              </div>
            </div>
          </div>
        </div>

        {/* Confidence Score */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-[#111827] rounded-lg p-4">
            <p className="text-sm text-[#9CA3AF] mb-1">AI Confidence</p>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-white">96%</span>
              <span className="text-xs text-green-400">High</span>
            </div>
          </div>
          <div className="bg-[#111827] rounded-lg p-4">
            <p className="text-sm text-[#9CA3AF] mb-1">Similar Issues Found</p>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-white">12</span>
              <span className="text-xs text-[#9CA3AF]">in codebase</span>
            </div>
          </div>
          <div className="bg-[#111827] rounded-lg p-4">
            <p className="text-sm text-[#9CA3AF] mb-1">Estimated Fix Time</p>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-white">5</span>
              <span className="text-xs text-[#9CA3AF]">minutes</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-4 mt-6">
          <button className="px-6 py-3 bg-gradient-to-r from-[#22C55E] to-[#16A34A] text-white rounded-lg hover:shadow-lg transition-all">
            Apply Fix
          </button>
          <button className="px-6 py-3 bg-[#111827] border border-[#374151] text-white rounded-lg hover:bg-[#374151] transition-all">
            View All Similar Issues
          </button>
        </div>
      </div>
    </div>
  );
}
