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


  useEffect(() => {
    const savedId = localStorage.getItem("conversation_id");
    console.log("Loaded conversation_id:", savedId);
    if (savedId) {
      setConversationId(Number(savedId));
    }
  }, []);


  useEffect(() => {
    if (!conversationId) return;

    const loadMessages = async () => {
      try {
        const res = await apiClient.get(
          `/conversations/${conversationId}/messages/`
        );
console.log("Fetching messages for:", conversationId);
        const formatted: ChatMessage[] = res.data.map((m: any) => ({
          role: m.role,
          content: m.content,
          sources: m.retrieved_documents || [],
        }));

        setMessages(formatted.slice(-10));
      } catch {
        console.error("Failed to load messages");
      }
    };

    loadMessages();
  }, [conversationId]);

  const startNewChat = () => {
    setMessages([]);
    setConversationId(null);
    localStorage.removeItem("conversation_id");
  };

  const renderAnswer = (answer: string, sources: Source[] = []) => {
    const parts = answer.split(/(\[\d+\])/g);

    return parts.map((part, i) => {
      const match = part.match(/\[(\d+)\]/);

      if (match) {
        const index = parseInt(match[1]);
        const source = sources.find((s) => s.index === index);

        return (
          <span key={i} className="text-blue-600 hover:underline">
            [{index}]
            {source && (
              <span className="ml-1 text-xs text-gray-500">
                ({source.title})
              </span>
            )}
          </span>
        );
      }

      return <span key={i}>{part}</span>;
    });
  };

  const sendQuestion = async () => {
    const q = question.trim();
    if (!q) return;

    setError("");
    setIsLoading(true);

    setMessages((prev) => {
      const newMessage: ChatMessage = {
        role: "user",
        content: q,
      };


      const updated = [...prev, newMessage];
      return updated.slice(-10);
    });

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

      if (newId) {
        setConversationId(newId);
        localStorage.setItem("conversation_id", String(newId));
      }

      setMessages((prev) => {
        const newMessage: ChatMessage = {
          role: "assistant",
          content: String(answer), // ensure string
          sources: sources || [],
        };

        const updated = [...prev, newMessage];
        return updated.slice(-10);
      });
    } 
    catch (err: any) {
      console.error("Error asking AI:", err);
      setError(
        err.response?.data?.error || "Failed to get answer from AI. Please try again."
      );
    }
    finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="border rounded-lg p-3 sm:p-4 bg-white shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-3 gap-2">
        <h3 className="text-base sm:text-lg font-semibold">Doubt Solver Chat</h3>

        <div className="flex flex-col sm:flex-row sm:items-center gap-2 w-full sm:w-auto">
          {conversationId && (
            <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600 whitespace-nowrap">
              #{conversationId}
            </span>
          )}

          <button
            onClick={startNewChat}
            className="w-full sm:w-auto text-xs bg-gray-200 px-3 py-2 rounded hover:bg-gray-300 text-left sm:text-center"
          >
            New Chat
          </button>
        </div>
      </div>

      <div className="space-y-2 mb-3 max-h-60 sm:max-h-72 overflow-auto">
        {messages.length === 0 ? (
          <div className="text-xs sm:text-sm text-gray-500">
            Ask a doubt and the AI will answer.
          </div>
        ) : (
          messages.map((message, i) => (
            <div
              key={`${message.role}-${i}`}
              className={`p-2 rounded-md text-xs sm:text-sm ${
                message.role === "user"
                  ? "bg-blue-50 border border-blue-200 text-blue-800"
                  : "bg-gray-50 border border-gray-200 text-gray-800"
              }`}
            >
              <div className="font-semibold text-xs mb-1">
                {message.role === "user" ? "You" : "AI"}
              </div>

              <div>
                {message.role === "assistant"
                  ? renderAnswer(message.content, message.sources || [])
                  : message.content}
              </div>
            </div>
          ))
        )}
      </div>

      {error && <div className="text-xs text-red-600 mb-2">{error}</div>}

      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        rows={3}
        placeholder="Ask your doubt..."
        className="w-full border rounded-md p-2 mb-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
      />

      <button
        onClick={sendQuestion}
        disabled={isLoading || !question.trim()}
        className="w-full sm:w-auto bg-black disabled:opacity-50 text-white rounded-md px-3 py-2 text-xs sm:text-sm hover:bg-black/80"
      >
        {isLoading ? "Generating..." : "Ask AI"}
      </button>
    </div>
  );
}