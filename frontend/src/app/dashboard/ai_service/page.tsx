"use client";

import { useState } from "react";
import { apiClient } from "@/lib/apiClient";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export default function AIServicePage() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const sendQuestion = async () => {
    const q = question.trim();
    if (!q) return;

    setError("");
    setIsLoading(true);

    const newMessages = [...messages, { role: "user", content: q }];
    setMessages(newMessages);
    setQuestion("");

    try {
      const payload: any = {
        question: q,
        context: "",
      };
      if (conversationId) {
        payload.conversation_id = conversationId;
      }

      const response = await apiClient.post("/ask-ai/", payload);

      const answer = response.data.answer;
      const newId = response.data.conversation_id;

      if (newId) {
        setConversationId(newId);
      }

      setMessages((prev) => [...prev, { role: "assistant", content: answer }]);
    } catch (e: any) {
      setError(
        e?.response?.data?.error || "Failed to get AI response. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">AI Service</h1>
      <p className="text-gray-600 mb-6">
        Ask questions powered by AI and RAG documents. Start a conversation and receive contextual answers based on your study materials.
      </p>

      <div className="bg-white rounded-xl shadow p-5 mb-6">
        <h2 className="text-xl font-semibold mb-3">Doubt Solver Chat</h2>

        <div className="space-y-2 mb-4">
          {messages.length === 0 && (
            <p className="text-sm text-gray-500">No messages yet. Ask your first doubt below.</p>
          )}
          {messages.map((msg, idx) => (
            <div
              key={`${msg.role}-${idx}`}
              className={`p-3 rounded-lg ${
                msg.role === "user"
                  ? "bg-blue-50 border border-blue-200"
                  : "bg-gray-50 border border-gray-200"
              }`}
            >
              <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">
                {msg.role === "user" ? "You" : "AI Tutor"}
              </div>
              <div className="text-sm text-gray-800">{msg.content}</div>
            </div>
          ))}
        </div>

        {error && <div className="text-red-600 mb-3">{error}</div>}

        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Type your doubt here..."
          className="w-full border rounded-lg p-3 mb-3 focus:outline-none focus:border-blue-500"
          rows={4}
        />

        <div className="flex items-center gap-2">
          <button
            onClick={sendQuestion}
            disabled={isLoading}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? "Thinking..." : "Send"}
          </button>
          {conversationId && (
            <span className="text-xs text-gray-500">Conversation #{conversationId}</span>
          )}
        </div>
      </div>
    </div>
  );
}