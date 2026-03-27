"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useMockTestDetail, useSubmitAnswer } from "@/features/mocktest/hooks/useMockTest";
import { apiClient } from "@/lib/apiClient";
import {useRouter} from "next/navigation";
import { finalizeTest } from "@/features/mocktest/services/mocktest.services";

export default function MockTestAttemptPage() {
  const params = useParams();
  const testId = Number(params.id);
  const router = useRouter();
  const { data, isLoading } = useMockTestDetail(testId);
  const { mutate } = useSubmitAnswer();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [selected, setSelected] = useState<Record<number, string>>({});
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [questionStartTime, setQuestionStartTime] = useState<number>(Date.now());
  const STORAGE_KEY = `mocktest_index_${testId}`;

  useEffect(() => {
  const startTest = async () => {
    try {
      await apiClient.post(`/mocktest/start/${testId}/`);
    } catch (err) {
      console.error("Failed to start test", err);
    }
  };

  if (testId) {
    startTest();
  }
}, [testId]);
  // ✅ Restore answers
  useEffect(() => {
    if (data?.answers) {
      const restored: Record<number, string> = {};
      data.answers.forEach((a: any) => {
        restored[a.question] = a.user_answer;
      });
      setSelected(restored);
    }
  }, [data]);

  // ✅ Restore current question index
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      setCurrentIndex(Number(saved));
    }
  }, [testId]);

  // ✅ Persist index on change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, String(currentIndex));
  }, [currentIndex]);

  // ✅ Initialize timer from backend
  useEffect(() => {
    if (data?.remaining_seconds !== undefined) {
      setTimeLeft(data.remaining_seconds);
    }
  }, [data]);

  // ✅ Countdown timer (stable)
  useEffect(() => {
    if (timeLeft === null) return;

    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev === null) return prev;

        if (prev <= 1) {
          clearInterval(interval);
          handleSubmit();
          return 0;
        }

        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [timeLeft]);

  useEffect(() => {
  setQuestionStartTime(Date.now());
}, [currentIndex]);
  // ✅ Prevent render before state is ready
  if (isLoading || !data || timeLeft === null) {
    return <div className="p-6">Loading...</div>;
  }

  const question = data.questions[currentIndex];

const handleSelect = (value: string) => {
  const timeTaken = Math.floor((Date.now() - questionStartTime) / 1000);

  setSelected((prev) => ({
    ...prev,
    [question.id]: value,
  }));

  mutate({
    attempt_id: data.attempt_id,
    question_id: question.id,
    user_answer: value,
    time_taken_seconds: timeTaken, // ✅ FIX
  });

  // reset timer after answering
  setQuestionStartTime(Date.now());
};

const handleSubmit = async () => {
  if (!data?.attempt_id) {
    alert("Test session expired. Please restart.");
    return;
  }

  await finalizeTest({
    attempt_id: data.attempt_id,
  });
  console.log(data.attempt_id)
  router.push(`/dashboard/mocktest/results/${data.attempt_id}`);
};

  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;

  return (
    <div className="flex">
      {/* Question Panel */}
      <div className="flex-1 p-6 space-y-6">
        {/* Timer */}
        <div className="text-right font-medium">
          Time Left: {minutes}:{seconds.toString().padStart(2, "0")}
        </div>

        <h2 className="font-semibold">
          Question {currentIndex + 1}
        </h2>

        <p>{question.question_text}</p>

        {/* Options */}
        {question.options.map((opt: any) => (
          <label
            key={opt.key}
            className="block border p-2 rounded mt-2 cursor-pointer"
          >
            <input
              type="radio"
              name={`q-${question.id}`}
              checked={selected[question.id] === opt.key}
              onChange={() => handleSelect(opt.key)}
              className="mr-2"
            />
            {opt.text}
          </label>
        ))}

        {/* Navigation */}
        <div className="flex justify-between mt-6">
          <button
            disabled={currentIndex === 0}
            onClick={() => setCurrentIndex((prev) => prev - 1)}
            className="px-4 py-2 border rounded"
          >
            Previous
          </button>

          <button
            disabled={currentIndex === data.questions.length - 1}
            onClick={() => setCurrentIndex((prev) => prev + 1)}
            className="px-4 py-2 border rounded"
          >
            Next
          </button>
        </div>

        <button
          onClick={handleSubmit}
          className="mt-4 bg-red-600 text-white px-4 py-2 rounded"
        >
          Submit Test
        </button>
      </div>

      {/* Navigation Panel */}
      <div className="w-64 border-l p-4 space-y-2">
        <h3 className="font-semibold">Questions</h3>

        <div className="grid grid-cols-5 gap-2">
          {data.questions.map((q: any, index: number) => (
            <button
              key={q.id}
              onClick={() => setCurrentIndex(index)}
              className={`p-2 rounded text-sm
                ${
                  selected[q.id]
                    ? "bg-green-500 text-white"
                    : "bg-gray-200"
                }`}
            >
              {index + 1}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}