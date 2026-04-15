'use client';

import { DocumentUpload, AskAIChat } from '@/features/ai/components';
import { useRequireAuth } from '@/features/auth';

export default function AIPageImproved() {
  const { user, isLoading } = useRequireAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">Loading...</div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 text-black px-4 sm:px-6 py-10">
      <div className="max-w-6xl mx-auto space-y-10">
        {/* HEADER */}
        <div className="text-center space-y-3">
          <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight">AI Workspace</h1>
          <p className="text-gray-500 max-w-xl mx-auto">
            Upload study materials and interact with AI for explanations, summaries, and problem
            solving
          </p>
        </div>

        {/* FEATURE CARDS */}
        <div className="grid items-start md:grid-cols-[0.85fr_1.15fr] lg:grid-cols-[0.75fr_1.25fr] gap-6">
          {/* UPLOAD CARD */}
          <div className="group relative self-start h-fit bg-white rounded-2xl p-4 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-transparent via-gray-50 to-transparent opacity-0 group-hover:opacity-100 transition" />

            <div className="relative z-10">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Upload Document</h2>
                <span className="text-xs px-2 py-1 bg-gray-100 rounded">PDF / DOC</span>
              </div>

              <p className="text-sm text-gray-500 mb-4">
                Add documents to extract knowledge and ask questions
              </p>

              <div className="border-2 border-dashed border-gray-200 rounded-xl p-3 hover:border-gray-400 transition">
                <DocumentUpload compact />
              </div>
            </div>
          </div>

          {/* CHAT CARD */}
          <div className="group relative bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-transparent via-gray-50 to-transparent opacity-0 group-hover:opacity-100 transition" />

            <div className="relative z-10 flex flex-col h-full">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Ask AI</h2>
                <span className="text-xs px-2 py-1 bg-black text-white rounded">Live</span>
              </div>

              <p className="text-sm text-gray-500 mb-4">
                Ask doubts, get explanations, and learn interactively
              </p>

              <div className="flex-1 min-h-[560px] border border-gray-200 rounded-xl p-3 bg-gray-50">
                <AskAIChat fill />
              </div>
            </div>
          </div>
        </div>

        {/* FOOTER NOTE */}
        <div className="text-center text-xs text-gray-400">
          Powered by AI • Context-aware responses • Fast retrieval
        </div>
      </div>
    </div>
  );
}
