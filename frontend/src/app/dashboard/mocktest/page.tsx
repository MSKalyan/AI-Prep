"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import {
  createMockTest,
  submitAnswer,
  finalizeTest,
} from "@/features/mocktest/services/mocktest.services";

export default function MockTestPage() {
  const searchParams = useSearchParams();
  const topicId = Number(searchParams.get("topicId"));

  const [test, setTest] = useState<any>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [result, setResult] = useState<any>(null);
  const [timeLeft, setTimeLeft] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 🔹 Create test using SERVICE
  useEffect(() => {
    if (!topicId) return;

    const initTest = async () => {
      try {
        const data = await createMockTest({
          topic_id: topicId,
          num_questions: 5,
    
        });

        setTest(data);
      } catch (err) {
        console.error("Error creating test:", err);
      }
    };

    initTest();
  }, [topicId]);

  // 🔹 Initialize timer
  useEffect(() => {
    if (test?.mock_test?.duration_minutes) {
      setTimeLeft(test.mock_test.duration_minutes * 60);
    }
  }, [test]);

  // 🔹 Countdown
  useEffect(() => {
    if (timeLeft <= 0) return;

    const interval = setInterval(() => {
      setTimeLeft((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [timeLeft]);

  // 🔹 Auto-submit
  useEffect(() => {
    if (timeLeft === 0 && test && !result) {
      handleSubmit();
    }
  }, [timeLeft]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  if (!test) return <div className="p-4">Loading test...</div>;

  const questions = test.mock_test?.questions || [];
  if (!questions.length) {
    return <div className="p-4">No questions available</div>;
  }

  const question = questions[currentIndex];
  const options = (question.options || {}) as Record<string, string>;

  const handleSelect = (questionId: number, optionKey: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: optionKey,
    }));
  };

  // 🔹 Submit using SERVICE
  const handleSubmit = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);

    try {
      const attemptId = test.attempt.id;

      // Submit answers
      for (const [questionId, option] of Object.entries(answers)) {
        await submitAnswer({
          attempt_id: attemptId,
          question_id: Number(questionId),
          user_answer: option,
        });
      }

      // Finalize test
      const data = await finalizeTest({
        attempt_id: attemptId,
      });

      setResult(data);
    } catch (err) {
      console.error("Submit error:", err);
    }
  };

  // 🔹 Result Screen
  if (result) {
    return (
      <div className="p-4">
        <h1 className="text-xl font-bold mb-4">Test Result</h1>

        <p>Score: {result.score} / {result.total_marks}</p>
        <p>Percentage: {result.percentage}%</p>
        <p>Correct: {result.correct}</p>
        <p>Incorrect: {result.incorrect}</p>
        <p>Unanswered: {result.unanswered}</p>

        <div className="mt-6">
          <h2 className="font-semibold mb-2">Review:</h2>

          {result.questions.map((q: any) => (
            <div key={q.question_id} className="mb-4 border p-3 rounded">
              <p className="font-medium">{q.question_text}</p>
              <p>Your Answer: {q.your_answer || "Not Answered"}</p>
              <p>Correct Answer: {q.correct_answer}</p>

              <p className={q.is_correct ? "text-green-600" : "text-red-600"}>
                {q.is_correct ? "Correct" : "Wrong"}
              </p>

              <p className="text-sm text-gray-600">
                {q.explanation}
              </p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // 🔹 Test UI
  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-2">
        {test.mock_test.title}
      </h1>

      <p className="mb-4 font-semibold text-red-600">
        Time Left: {formatTime(timeLeft)}
      </p>

      <p className="mb-4">
        Question {currentIndex + 1} of {questions.length}
      </p>

      <h2 className="font-semibold mb-4">
        {question.question_text}
      </h2>

      <div className="space-y-2">
        {Object.entries(options).map(([key, value]) => (
          <label key={key} className="block border p-2 rounded cursor-pointer">
            <input
              type="radio"
              name={`q-${question.id}`}
              checked={answers[question.id] === key}
              onChange={() => handleSelect(question.id, key)}
              className="mr-2"
            />
            {key}. {value}
          </label>
        ))}
      </div>

      <div className="flex justify-between mt-6">
        <button
          disabled={currentIndex === 0}
          onClick={() => setCurrentIndex((prev) => prev - 1)}
          className="px-4 py-2 bg-gray-300 rounded"
        >
          Previous
        </button>

        <button
          disabled={currentIndex === questions.length - 1}
          onClick={() => setCurrentIndex((prev) => prev + 1)}
          className="px-4 py-2 bg-blue-600 text-white rounded"
        >
          Next
        </button>
      </div>

      <button
        disabled={isSubmitting}
        onClick={handleSubmit}
        className="mt-6 px-6 py-2 bg-green-600 text-white rounded"
      >
        Submit Test
      </button>

      <div className="grid grid-cols-5 gap-2 mt-6">
        {questions.map((q: any, index: number) => (
          <button
            key={q.id}
            onClick={() => setCurrentIndex(index)}
            className={`p-2 rounded ${
              answers[q.id]
                ? "bg-green-500 text-white"
                : "bg-gray-200"
            }`}
          >
            {index + 1}
          </button>
        ))}
      </div>
    </div>
  );
}