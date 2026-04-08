import DocumentUpload from "@/features/ai/components/DocumentUpload";
import AskAIChat from "@/features/ai/components/AskAIChat";

export default function AIPage() {
  return (
    <div className="min-h-screen bg-white text-black px-4 sm:px-6 py-6 sm:py-10">
      
      {/* Page Container */}
      <div className="max-w-6xl mx-auto space-y-10">

        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-semibold tracking-tight">
            AI Workspace
          </h1>
          <p className="text-sm sm:text-base text-gray-600">
            Upload documents and interact with AI seamlessly
          </p>
        </div>

        {/* Sections */}
        <div className="grid md:grid-cols-2 gap-6">

          {/* Upload Card */}
          <div className="border border-gray-200 rounded-2xl p-4 sm:p-6 shadow-sm hover:shadow-md transition">
            <h2 className="text-lg font-medium mb-4">Upload Document</h2>
            <DocumentUpload />
          </div>

          {/* Chat Card */}
          <div className="border border-gray-200 rounded-2xl p-4 sm:p-6 shadow-sm hover:shadow-md transition">
            <h2 className="text-lg font-medium mb-4">Ask AI</h2>
            <AskAIChat />
          </div>

        </div>

      </div>
    </div>
  );
}