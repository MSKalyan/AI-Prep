'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useGenerateRoadmap } from '../hooks/useRoadmap';
import { useExams } from '../hooks/useExams';

interface Exam {
  id: number;
  name: string;
  exam_date: string;
}

export default function CreateRoadmapForm() {
  const router = useRouter();
  const { generateRoadmap } = useGenerateRoadmap();
  const examsQuery = useExams();
  const exams = examsQuery.data;

  const [form, setForm] = useState({
    exam_id: '',
    target_date: '',
    study_hours_per_day: 4,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');

    if (!form.exam_id) {
      setError('Please select an exam.');
      return;
    }

    if (!form.target_date) {
      setError('Please select a target date.');
      return;
    }

    const selectedDate = new Date(form.target_date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const selectedExam = exams?.find((exam: Exam) => exam.id === Number(form.exam_id));

    if (selectedDate <= today) {
      setError('Target date must be in the future.');
      return;
    }

    if (selectedExam?.exam_date && selectedDate > new Date(selectedExam.exam_date)) {
      setError(`Target date must be on or before the exam date (${selectedExam.exam_date}).`);
      return;
    }

    try {
      setLoading(true);
      const response = await generateRoadmap({
        exam_id: Number(form.exam_id),
        target_date: form.target_date,
        study_hours_per_day: form.study_hours_per_day,
      });
      router.push(`/dashboard/roadmap/${response.roadmap_id}`);
    } catch {
      setError('Failed to generate roadmap.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex justify-center px-4 sm:px-6 py-6">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md space-y-4 rounded-lg border bg-white p-4 sm:p-6 shadow-md"
      >
        <h2 className="text-xl font-semibold text-gray-800">Create Study Roadmap</h2>

        <div>
          <label htmlFor="exam_id" className="mb-1 block text-sm text-gray-600">Select Exam</label>
          <select
            id="exam_id"
            className="w-full rounded-md border p-2 focus:border-blue-500 focus:outline-none"
            value={form.exam_id}
            onChange={(e) => setForm({ ...form, exam_id: e.target.value })}
            disabled={false}
            required
          >
            <option value="">-- Select Exam --</option>
            {exams?.map((exam: Exam) => (
              <option key={exam.id} value={exam.id}>
                {exam.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="target_date" className="mb-1 block text-sm text-gray-600">Target Date</label>
          <input
            id="target_date"
            type="date"
            required
            className="w-full rounded-md border p-2"
            value={form.target_date}
            onChange={(e) => setForm({ ...form, target_date: e.target.value })}
          />
          {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
        </div>

        <div>
          <label htmlFor="study_hours_per_day" className="mb-1 block text-sm text-gray-600">Study Hours Per Day</label>
          <input
            id="study_hours_per_day"
            type="number"
            min={1}
            max={24}
            required
            className="w-full rounded-md border p-2"
            value={form.study_hours_per_day}
            onChange={(e) => setForm({ ...form, study_hours_per_day: Number(e.target.value) })}
          />
        </div>

        <button
          type="submit"
          className="w-full rounded-md bg-black px-4 py-2 text-white"
          disabled={loading}
        >
          {loading ? 'Generating...' : 'Generate Roadmap'}
        </button>
      </form>
    </div>
  );
}
