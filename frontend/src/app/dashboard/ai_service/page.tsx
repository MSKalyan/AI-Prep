export default function AIServicePage() {
  return (
    <div className="max-w-4xl">
      
      <h1 className="text-3xl font-bold mb-6">
        AI Service
      </h1>

      <p className="text-gray-600 mb-8">
        Ask questions powered by AI and RAG documents. Start a conversation
        and receive contextual answers based on your study materials.
      </p>

      {/* AI Chat Entry Section */}
      <div className="bg-white rounded-xl shadow-md p-6">

        <h2 className="text-lg font-semibold mb-4">
          Start Conversation
        </h2>

        <textarea
          placeholder="Ask something..."
          className="w-full border rounded-lg p-3 mb-4 focus:outline-none"
          rows={4}
        />

        <button className="bg-blue-600 text-white px-5 py-2 rounded-lg hover:bg-blue-700 transition">
          Send
        </button>

      </div>

    </div>
  );
}