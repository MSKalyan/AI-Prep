"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

import { useGenerateRoadmap } from "@/features/roadmap/hooks/useGenerateRoadmap";
import { useRoadmapJob } from "@/features/roadmap/hooks/useRoadmapJob";

import CreateRoadmapForm from "@/features/roadmap/components/CreateRoadmapForm";

export default function RoadmapPage(){

  const router = useRouter();

  const [jobId,setJobId] = useState<number | undefined>();

  const { createRoadmap } = useGenerateRoadmap();

  const jobQuery = useRoadmapJob(jobId);

  // 🚀 redirect when completed

  useEffect(()=>{

    if(jobQuery.data?.status === "completed" && jobQuery.data.roadmap_id){

      router.push(`/roadmap/${jobQuery.data.roadmap_id}`);

    }

  },[jobQuery.data,router]);

  const handleCreate = async(payload:any)=>{

    const res = await createRoadmap(payload);

    setJobId(res.job_id);

  };

  return (

    <div className="p-6">

      <CreateRoadmapForm createRoadmap={handleCreate}/>

      {jobQuery.data?.status === "pending" && (
        <p>Generating roadmap...</p>
      )}

    </div>

  );
}
