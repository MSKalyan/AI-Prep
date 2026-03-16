"use client";

import { useState } from "react";
import { apiClient } from "@/lib/apiClient";

interface AskAIChatProps {
  context?: string;
}

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export default function AskAIChat({ context = "" }: AskAIChatProps) {
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

    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setQuestion("");

    try {
      const payload: any = {
        question: q,
        context: context || "",
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
      setError(e?.response?.data?.error || "Failed to fetch AI response.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold">Doubt Solver Chat</h3>
        {conversationId && (
          <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600">
            Conversation #{conversationId}
          </span>
        )}
      </div>

      <div className="space-y-2 mb-3 max-h-72 overflow-auto">
        {messages.length === 0 ? (
          <div className="text-sm text-gray-500">Ask a doubt and the AI will answer from relevant context.</div>
        ) : (
          messages.map((message, i) => (
            <div
              key={`${message.role}-${i}`}
              className={`p-2 rounded-md text-sm ${
                message.role === "user"
                  ? "bg-blue-50 border border-blue-200 text-blue-800"
                  : "bg-gray-50 border border-gray-200 text-gray-800"
              }`}
            >
              <div className="font-semibold text-xs uppercase tracking-wide mb-1">
                {message.role === "user" ? "You" : "AI Tutor"}
              </div>
              <div>{message.content}</div>
            </div>
          ))
        )}
      </div>

      {error && <div className="text-xs text-red-600 mb-2">{error}</div>}

      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        rows={3}
        placeholder="Ask your study doubt here..."
        className="w-full border rounded-md p-2 mb-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
      />

      <button
        onClick={sendQuestion}
        disabled={isLoading || !question.trim()}
        className="bg-blue-600 disabled:opacity-50 text-white rounded-md px-3 py-2 text-sm hover:bg-blue-700 transition"
      >
        {isLoading ? "Generating answer..." : "Ask AI"}
      </button>
    </div>
  );
}
