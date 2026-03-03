"use client";

import { useState } from "react";

interface Props {
  createTest: (payload:any)=>Promise<any>;
}

export default function CreateMockTestForm({ createTest }: Props) {

  const [form, setForm] = useState({
    title: "",
    exam_type: "",
    subject: "",
    difficulty: "medium",
    num_questions: 10,
    duration_minutes: 60
  });

  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e:React.FormEvent)=>{

    e.preventDefault();

    if(!form.exam_type || !form.subject) return;

    try{

      setLoading(true);

      await createTest(form);

    } finally{
      setLoading(false);
    }
  };

  return (

    <form
      onSubmit={handleSubmit}
      className="space-y-4 max-w-md bg-white border p-6 rounded shadow"
    >

      <h2 className="text-lg font-semibold">
        Create Mock Test
      </h2>

      {/* Title */}
      <input
        placeholder="Test title"
        value={form.title}
        onChange={(e)=>setForm({...form,title:e.target.value})}
        className="w-full border p-2 rounded"
      />

      {/* Exam Type */}
      <input
        placeholder="Exam Type (e.g. UPSC)"
        value={form.exam_type}
        onChange={(e)=>setForm({...form,exam_type:e.target.value})}
        className="w-full border p-2 rounded"
        required
      />

      {/* Subject */}
      <input
        placeholder="Subject"
        value={form.subject}
        onChange={(e)=>setForm({...form,subject:e.target.value})}
        className="w-full border p-2 rounded"
        required
      />

      {/* Difficulty */}
      <select
        value={form.difficulty}
        onChange={(e)=>setForm({...form,difficulty:e.target.value})}
        className="w-full border p-2 rounded"
      >
        <option value="easy">Easy</option>
        <option value="medium">Medium</option>
        <option value="hard">Hard</option>
      </select>

      {/* Questions */}
      <input
        type="number"
        min={1}
        max={50}
        value={form.num_questions}
        onChange={(e)=>setForm({...form,num_questions:Number(e.target.value)})}
        className="w-full border p-2 rounded"
      />

      {/* Duration */}
      <input
        type="number"
        min={1}
        value={form.duration_minutes}
        onChange={(e)=>setForm({...form,duration_minutes:Number(e.target.value)})}
        className="w-full border p-2 rounded"
      />

      <button
        type="submit"
        disabled={loading}
        className="bg-blue-600 text-white w-full py-2 rounded"
      >
        {loading ? "Creating..." : "Start Mock Test"}
      </button>

    </form>
  );
}