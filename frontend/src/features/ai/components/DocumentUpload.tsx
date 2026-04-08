"use client";

import { apiClient } from "@/lib/apiClient";
import { useState } from "react";

export default function DocumentUpload() {
const [file, setFile] = useState<File | null>(null);
  const [subject, setSubject] = useState("");
  const [examType, setExamType] = useState("");
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
  formData.append("file", file);
formData.append("title", file.name);
formData.append("subject", subject);
formData.append("topic", "general"); // or input field
formData.append("exam_type", examType);
formData.append("document_type", "notes");
    try {
      setLoading(true);

      const res = await apiClient("http://localhost:8000/api/documents/process/", {
        method: "POST",
        data: formData,
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      const data = await res.data;
      console.log(data);
      alert("Processed successfully");
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 sm:p-6 border rounded-xl">
      <h2 className="font-semibold text-base sm:text-lg mb-4 sm:mb-6">Upload Document</h2>

      <div className="space-y-3 sm:space-y-4">
        <input 
          type="file" 
          accept=".pdf,.doc,.docx,.txt,.md" 
          className="block w-full text-sm"
          onChange={(e) => setFile(e.target.files?.[0] || null)} 
        />

        <input
          placeholder="Subject"
          className="block w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
        />

        <input
          placeholder="Exam"
          className="block w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          value={examType}
          onChange={(e) => setExamType(e.target.value)}
        />

        <button
          onClick={handleUpload}
          className="w-full mt-4 px-4 py-2 bg-black text-white rounded text-sm sm:text-base hover:opacity-80 transition disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Processing..." : "Upload & Process"}
        </button>
      </div>
    </div>
  );
}