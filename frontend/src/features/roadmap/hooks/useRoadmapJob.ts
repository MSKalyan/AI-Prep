import { useQuery } from "@tanstack/react-query";
import * as roadmap from "../services/roadmap.service";

// export function useRoadmapJob(jobId?: number) {

//   return useQuery({
//     queryKey: ["roadmap-job", jobId],
//     queryFn: () => roadmap.getRoadmapJob(jobId!),
//     enabled: !!jobId,

//     refetchInterval: (query) =>
//       query.state.data?.status === "completed"
//         ? false
//         : 3000
//   });
// }

export function useRoadmaps() {
  return useQuery({
    queryKey:["roadmaps"],
    queryFn: roadmap.getRoadmaps
  });
}