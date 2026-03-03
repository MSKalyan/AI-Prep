"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useMockTestDetail, useSubmitAnswer } from "@/features/mocktest/hooks/useMockTest";
import { apiClient } from "@/lib/apiClient";

export default function MockTestAttemptPage() {

  const params = useParams();
  const testId = Number(params.id);

  const { data, isLoading } = useMockTestDetail(testId);
  const { mutate } = useSubmitAnswer();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [selected, setSelected] = useState<Record<number,string>>({});
  const [timeLeft, setTimeLeft] = useState<number | null>(null);

  
  // Restore answers
  useEffect(()=>{
            console.log(data);

    if(data?.answers){
      const restored:Record<number,string> = {};
      data.answers.forEach((a:any)=>{
        restored[a.question] = a.user_answer;
      });
      setSelected(restored);
    }
  },[data]);

  // Initialize timer
  useEffect(()=>{
    if(data?.duration_minutes){
      setTimeLeft(data.duration_minutes * 60);
    }
  },[data]);

  // Countdown
  useEffect(()=>{
    if(timeLeft === null) return;

    if(timeLeft <= 0){
      handleSubmit();
      return;
    }

    const timer = setInterval(()=>{
      setTimeLeft(prev => prev! - 1);
    },1000);

    return ()=>clearInterval(timer);
  },[timeLeft]);

  if(isLoading || !data) return <div className="p-6">Loading...</div>;

  const question = data.questions[currentIndex];

  const handleSelect = (value:string)=>{
    setSelected(prev=>({
      ...prev,
      [question.id]: value
    }));

    mutate({
      attempt_id: data.attempt_id,
      question_id: question.id,
      user_answer: value
    });
  };

  const handleSubmit = async ()=>{
    await apiClient.post("/results/", {
      attempt_id: data.attempt_id
    });
    window.location.href = "/dashboard/mocktest/results";
  };

  const minutes = Math.floor((timeLeft ?? 0) / 60);
  const seconds = (timeLeft ?? 0) % 60;

  return (

    <div className="flex">

      {/* Question Panel */}
      <div className="flex-1 p-6 space-y-6">

        {/* Timer */}
        <div className="text-right font-medium">
          Time Left: {minutes}:{seconds.toString().padStart(2,"0")}
        </div>

        <h2 className="font-semibold">
          Question {currentIndex + 1}
        </h2>

        <p>{question.question_text}</p>

        {["a","b","c","d"].map(opt=>(
          <label key={opt} className="block border p-2 rounded mt-2 cursor-pointer">
            <input
              type="radio"
              name={`q-${question.id}`}
              checked={selected[question.id] === opt.toUpperCase()}
              onChange={()=>handleSelect(opt.toUpperCase())}
              className="mr-2"
            />
            {question[`option_${opt}`]}
          </label>
        ))}

        <div className="flex justify-between mt-6">
          <button
            disabled={currentIndex===0}
            onClick={()=>setCurrentIndex(prev=>prev-1)}
            className="px-4 py-2 border rounded"
          >
            Previous
          </button>

          <button
            disabled={currentIndex===data.questions.length-1}
            onClick={()=>setCurrentIndex(prev=>prev+1)}
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
          {data.questions.map((q:any,index:number)=>(
            <button
              key={q.id}
              onClick={()=>setCurrentIndex(index)}
              className={`p-2 rounded text-sm
                ${selected[q.id] ? "bg-green-500 text-white" : "bg-gray-200"}
              `}
            >
              {index+1}
            </button>
          ))}
        </div>

      </div>

    </div>
  );
}