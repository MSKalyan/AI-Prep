'use client';

import { useParams, useRouter } from 'next/navigation';
import { useState } from 'react';
import {
  useMockTestDetail,
  useSubmitAnswer,
  useMockTestController,
  useCountdown,
  useSelectedAnswers,
  useQuestionIndex,
} from '@/features/mocktest';
import { finalizeTest } from '@/features/mocktest/services';

interface Option {
  key: string;
  text: string;
}

interface Question {
  id: number;
  question_text: string;
  options: Option[];
}

function MockTestAttemptContent({
  testId,
  data,
}: {
  testId: number;
  data: {
    attempt_id: number;
    remaining_seconds: number;
    questions: Question[];
  };
}) {
  const router = useRouter();
  const { mutate } = useSubmitAnswer();

  useMockTestController(testId);
  const { currentIndex, setCurrentIndex } = useQuestionIndex(testId);
  const { selected, setSelected } = useSelectedAnswers(data);

  const [questionStartTime, setQuestionStartTime] = useState(() => Date.now());

  const handleSubmit = async () => {
    if (!data?.attempt_id) return;
    await finalizeTest({ attempt_id: data.attempt_id });
    router.push(`/dashboard/mocktest/results/${data.attempt_id}`);
  };

  const timeLeft = useCountdown(data?.remaining_seconds, handleSubmit);

  if (timeLeft === null) {
    return <div className="p-6">Loading...</div>;
  }

  const question = data.questions[currentIndex];

  const handleSelect = (value: string) => {
    // eslint-disable-next-line react-hooks/purity
    const timeTaken = Math.floor((Date.now() - questionStartTime) / 1000);

    setSelected((prev) => ({
      ...prev,
      [question.id]: value,
    }));

    mutate({
      attempt_id: data.attempt_id,
      question_id: question.id,
      user_answer: value,
      time_taken_seconds: timeTaken,
    });

    // eslint-disable-next-line react-hooks/purity
    setQuestionStartTime(Date.now());
  };

  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;

  return (
    <div className="flex h-screen bg-gray-100">
      {/* LEFT: Question Panel */}
      <div className="flex-1 p-6 flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-xl font-semibold">Mock Test</h1>
          <div className="bg-black text-white px-4 py-2 rounded-lg font-mono">
            {minutes}:{seconds.toString().padStart(2, '0')}
          </div>
        </div>

        {/* Question Card */}
        <div className="bg-white rounded-2xl shadow p-6 flex-1 flex flex-col">
          <h2 className="text-lg font-medium mb-4">Question {currentIndex + 1}</h2>

          <p className="mb-6 text-gray-800 leading-relaxed">{question.question_text}</p>

          <div className="space-y-3">
            {question.options.map((opt: Option) => (
              <label
                key={opt.key}
                className={`border rounded-lg p-3 cursor-pointer flex items-center gap-3 transition ${
                  selected[question.id] === opt.key
                    ? 'border-black bg-gray-50'
                    : 'hover:border-gray-400'
                }`}
              >
                <input
                  type="radio"
                  className="accent-black"
                  checked={selected[question.id] === opt.key}
                  onChange={() => handleSelect(opt.key)}
                />
                <span>{opt.text}</span>
              </label>
            ))}
          </div>

          {/* Navigation */}
          <div className="flex justify-between mt-6">
            <button
              disabled={currentIndex === 0}
              onClick={() => setCurrentIndex((prev) => prev - 1)}
              className="px-4 py-2 border rounded-lg disabled:opacity-40"
            >
              Previous
            </button>

            {currentIndex === data.questions.length - 1 ? (
              <button onClick={handleSubmit} className="px-6 py-2 bg-black text-white rounded-lg">
                Submit Test
              </button>
            ) : (
              <button
                onClick={() => setCurrentIndex((prev) => prev + 1)}
                className="px-6 py-2 bg-black text-white rounded-lg"
              >
                Next
              </button>
            )}
          </div>
        </div>
      </div>

      {/* RIGHT: Question Palette */}
      <div className="w-80 bg-white border-l p-4 overflow-y-auto">
        <h3 className="font-semibold mb-4">Questions</h3>

        <div className="grid grid-cols-5 gap-2">
          {data.questions.map((q: Question, index: number) => {
            const isAnswered = !!selected[q.id];
            const isActive = index === currentIndex;

            let buttonClass = 'h-10 rounded-lg text-sm font-medium bg-gray-100';
            if (isActive) {
              buttonClass = 'h-10 rounded-lg text-sm font-medium bg-black text-white';
            } else if (isAnswered) {
              buttonClass = 'h-10 rounded-lg text-sm font-medium bg-green-100';
            }

            return (
              <button key={q.id} onClick={() => setCurrentIndex(index)} className={buttonClass}>
                {index + 1}
              </button>
            );
          })}
        </div>

        {/* Legend */}
        <div className="mt-6 space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-black"></div> Current
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-200"></div> Answered
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-gray-200"></div> Not Answered
          </div>
        </div>
      </div>
    </div>
  );
}

export default function MockTestAttemptPage() {
  const params = useParams();
  const testId = Number(params.id);
  const router = useRouter();

  const { data, isLoading, isError, error } = useMockTestDetail(testId);

  if (isError) {
    console.error('Failed to load mock test detail', error);
    return (
      <div className="p-6 space-y-3">
        <div className="text-lg font-semibold">Unable to load mock test</div>
        <div className="text-sm text-gray-600">
          Please go back and try again. If this keeps happening, the test may have invalid questions.
        </div>
        <button
          onClick={() => router.replace('/dashboard')}
          className="px-4 py-2 bg-black text-white rounded-lg"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  if (isLoading || !data) {
    return <div className="p-6">Loading...</div>;
  }

  return <MockTestAttemptContent testId={testId} data={data} />;
}
