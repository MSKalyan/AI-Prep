export interface RoadmapTopic {
  id: number;
  week_number: number;
  title: string;
  description: string;
  estimated_hours: number;
  resources: any[]; // JSONField
  priority: number;

  is_completed: boolean;
  completed_at: string | null;

  created_at: string;
}


export interface Roadmap {
  id: number;
  exam_name: string;
  target_date: string;
  difficulty_level: "beginner" | "intermediate" | "advanced";
  total_weeks: number;
  description: string;

  created_at: string;
  updated_at: string;

  topics: RoadmapTopic[];
}


