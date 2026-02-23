import { useQuery } from "@tanstack/react-query";
import { getRoadmapJob } from "../services/roadmap.service";

export function useRoadmapJob(jobId?: number){

  return useQuery({

    queryKey:["roadmap-job", jobId],

    queryFn: () => getRoadmapJob(jobId!),

    enabled: !!jobId,

    refetchInterval: (query) => {

      const data = query.state.data;

      if(!data) return 2000;

      if(data.status === "completed") return false;
      if(data.status === "failed") return false;

      return 2000;
    }
  });
}
