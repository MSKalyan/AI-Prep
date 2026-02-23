"use client";

import { useState } from "react";

interface Props {
  createRoadmap: (payload:any) => Promise<any>;
}

export default function CreateRoadmapForm({ createRoadmap }: Props){

  const [form,setForm] = useState({
    exam_id: "",
    target_date: "",
    difficulty_level: "intermediate",
    study_hours_per_day: 4,
    target_marks: 70,
    current_knowledge: ""
  });

  const [loading,setLoading] = useState(false);

  const handleSubmit = async (e:React.FormEvent) => {

    e.preventDefault();

    try{

      setLoading(true);

      await createRoadmap({
        ...form,
        exam_id: Number(form.exam_id),
      });

    } finally{

      setLoading(false);

    }
  };

  return (

    <div className="flex justify-center p-6">

      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md space-y-4 rounded-lg border bg-white p-6 shadow-md"
      >

        <h2 className="text-xl font-semibold text-gray-800">
          Create Study Roadmap
        </h2>

        {/* Exam ID (temporary input — later dropdown) */}

        <div>
          <label className="mb-1 block text-sm text-gray-600">
            Exam ID
          </label>

          <input
            type="number"
            className="w-full rounded-md border p-2 focus:border-blue-500 focus:outline-none"
            placeholder="Enter exam ID"
            value={form.exam_id}
            onChange={(e)=>setForm({...form,exam_id:e.target.value})}
            required
          />
        </div>

        {/* Target Date */}

        <div>
          <label className="mb-1 block text-sm text-gray-600">
            Target Date
          </label>

          <input
            type="date"
            className="w-full rounded-md border p-2 focus:border-blue-500 focus:outline-none"
            value={form.target_date}
            onChange={(e)=>setForm({...form,target_date:e.target.value})}
            required
          />
        </div>

        {/* Difficulty */}

        <div>
          <label className="mb-1 block text-sm text-gray-600">
            Difficulty Level
          </label>

          <select
            className="w-full rounded-md border p-2 focus:border-blue-500 focus:outline-none"
            value={form.difficulty_level}
            onChange={(e)=>setForm({...form,difficulty_level:e.target.value})}
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>

        {/* Study hours */}

        <div>
          <label className="mb-1 block text-sm text-gray-600">
            Study Hours Per Day
          </label>

          <input
            type="number"
            min={1}
            max={24}
            className="w-full rounded-md border p-2 focus:border-blue-500 focus:outline-none"
            value={form.study_hours_per_day}
            onChange={(e)=>setForm({...form,study_hours_per_day:Number(e.target.value)})}
          />
        </div>

        {/* Target Marks */}

        <div>
          <label className="mb-1 block text-sm text-gray-600">
            Target Marks
          </label>

          <input
            type="number"
            className="w-full rounded-md border p-2 focus:border-blue-500 focus:outline-none"
            value={form.target_marks}
            onChange={(e)=>setForm({...form,target_marks:Number(e.target.value)})}
          />
        </div>

        {/* Current Knowledge */}

        <div>
          <label className="mb-1 block text-sm text-gray-600">
            Current Knowledge (Optional)
          </label>

          <textarea
            className="w-full rounded-md border p-2 focus:border-blue-500 focus:outline-none"
            rows={3}
            value={form.current_knowledge}
            onChange={(e)=>setForm({...form,current_knowledge:e.target.value})}
          />
        </div>

        {/* Submit */}

        <button
          type="submit"
          className="w-full rounded-md bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Generating roadmap..." : "Generate Roadmap"}
        </button>

      </form>

    </div>
  );
}
