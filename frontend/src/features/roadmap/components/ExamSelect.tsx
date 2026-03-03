"use client";

import { useExams } from "../hooks/useExams";

interface Exam {
  id: number;
  name: string;
}

interface Props {
  value: string;
  onChange: (value: string) => void;
}

export default function ExamSelect({ value, onChange }: Props) {

  const { exams, isLoading, error } = useExams();

  return (

    <div>

      <label className="mb-1 block text-sm text-gray-600">
        Select Exam
      </label>

      <select
        className="w-full rounded-md border p-2 focus:border-blue-500 focus:outline-none"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={isLoading || !!error}
        required
      >

        <option value="">
          {isLoading ? "Loading exams..." : "-- Select Exam --"}
        </option>

        {exams?.map((exam: Exam) => (
          <option key={exam.id} value={exam.id}>
            {exam.name}
          </option>
        ))}

      </select>

      {error && (
        <p className="mt-1 text-xs text-red-500">
          Failed to load exams
        </p>
      )}

    </div>
  );
}