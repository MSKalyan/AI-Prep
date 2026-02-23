import { apiClient } from "@/lib/apiClient";
import { Roadmap } from "../types";
export async function generateRoadmap(payload:any){

  try{

    const res = await apiClient.post("/roadmap/generate/", payload);

    return res.data;

  }catch(error:any){

    console.log("API ERROR:", error.response?.data);

    throw error;
  }
}


export async function getRoadmapJob(jobId:number){

  const { data } = await apiClient.get(
    `/roadmap/job/${jobId}/`
  );

  return data;
}
