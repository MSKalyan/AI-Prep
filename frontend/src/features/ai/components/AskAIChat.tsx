"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/apiClient";

interface AskAIChatProps {
  context?: string;
}

type Source = {
  index: number;
  title: string;
  subject: string;
  content: string;
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
};

export default function AskAIChat({ context = "" }: AskAIChatProps) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  // 🔥 floating citation box
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  const [popupPosition, setPopupPosition] = useState({ x: 0, y: 0 });

  // =========================
  // 🔥 CLOSE ON OUTSIDE CLICK
  // =========================
  useEffect(() => {
    const handleClick = () => setSelectedSource(null);
    if (selectedSource) {
      window.addEventListener("click", handleClick);
    }
    return () => window.removeEventListener("click", handleClick);
  }, [selectedSource]);

  // =========================
  // 🔥 RENDER ANSWER WITH CITATIONS
  // =========================
  const renderAnswer = (answer: string, sources: Source[] = []) => {
    const parts = answer.split(/(\[\d+\])/g);

    return parts.map((part, i) => {
      const match = part.match(/\[(\d+)\]/);

      if (match) {
        const index = parseInt(match[1]);
        const source = sources.find((s) => s.index === index);

        return (
        <span
  key={i}
  className="relative text-blue-600 cursor-pointer hover:underline group"
>
  [{index}]

  {source && (
    <div
      className="
        absolute z-50 hidden group-hover:block
        bg-white border shadow-lg rounded-md p-2 text-xs w-64
        left-1/2 -translate-x-1/2 mt-1
      "
    >
      <div className="font-semibold text-[11px] mb-1">
        {source.title}
      </div>

      <div className="text-[10px] text-gray-500 mb-1">
        {source.subject}
      </div>

      <div className="text-[11px] text-gray-700 max-h-32 overflow-auto">
        {source.content}
      </div>
    </div>
  )}
</span>
        );
      }

      return <span key={i}>{part}</span>;
    });
  };

  // =========================
  // 🔥 SEND QUESTION
  // =========================
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
      const sources: Source[] = response.data.retrieved_documents || [];

      if (newId) setConversationId(newId);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: answer,
          sources: sources,
        },
      ]);
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
          <div className="text-sm text-gray-500">
            Ask a doubt and the AI will answer from relevant context.
          </div>
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
              <div className="font-semibold text-xs uppercase mb-1">
                {message.role === "user" ? "You" : "AI Tutor"}
              </div>

              <div>
                {message.role === "assistant"
                  ? renderAnswer(message.content, message.sources || [])
                  : message.content}
              </div>

              {/* sources list */}
              {message.role === "assistant" &&
                (message.sources || []).length > 0 && (
                  <div className="mt-2 text-xs text-gray-500">
                    {message.sources!.map((src) => (
                      <div key={src.index}>
                        [{src.index}] {src.title}
                      </div>
                    ))}
                  </div>
                )}
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

      {/* =========================
          🔥 FLOATING CITATION BOX
         ========================= */}
      {selectedSource && (
        <div
          className="fixed z-50 bg-white border rounded-lg shadow-lg p-3 text-sm w-72"
          style={{
            top: popupPosition.y + 10,
            left: popupPosition.x + 10,
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex justify-between items-start mb-1">
            <div className="font-semibold text-xs">
              {selectedSource.title}
            </div>
            <button
              onClick={() => setSelectedSource(null)}
              className="text-gray-400 hover:text-black text-xs"
            >
              ✕
            </button>
          </div>

          <div className="text-xs text-gray-500 mb-1">
            {selectedSource.subject}
          </div>

          <div className="text-xs text-gray-700 max-h-40 overflow-auto">
            {selectedSource.content}
          </div>
        </div>
      )}
    </div>
  );
}