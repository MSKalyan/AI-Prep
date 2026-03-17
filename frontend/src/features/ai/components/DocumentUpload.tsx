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
    <div className="p-4 border rounded-xl">
      <h2 className="font-semibold mb-2">Upload Document</h2>

      <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />

      <input
        placeholder="Subject"
        className="block mt-2 border p-1"
        value={subject}
        onChange={(e) => setSubject(e.target.value)}
      />

      <input
        placeholder="Exam Type"
        className="block mt-2 border p-1"
        value={examType}
        onChange={(e) => setExamType(e.target.value)}
      />

      <button
        onClick={handleUpload}
        className="mt-3 px-3 py-1 bg-blue-500 text-white rounded"
      >
        {loading ? "Processing..." : "Upload & Process"}
      </button>
    </div>
  );
}