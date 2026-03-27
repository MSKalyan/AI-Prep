"use client";

import { useStudyPlan } from "@/features/analytics/hooks/hooks";
import { StudyPlanItem } from "@/features/analytics/services/analytics.services";

export default function StudyPlanPage() {
  const { data = [], isLoading } = useStudyPlan();

  if (isLoading) return <div className="p-6">Loading...</div>;

  const top3 = data.slice(0, 3);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Study Plan</h1>

      <div>
        <h2>Focus Now</h2>
        <div className="grid md:grid-cols-3 gap-4">
          {top3.map((t) => (
            <Card key={t.topic_id} topic={t} highlight />
          ))}
        </div>
      </div>

      <div>
        <h2>All Topics</h2>
        {data.map((t) => (
          <Card key={t.topic_id} topic={t} />
        ))}
      </div>
    </div>
  );
}

function Card({
  topic,
  highlight,
}: {
  topic: StudyPlanItem;
  highlight?: boolean;
}) {
  return (
    <div className={`p-4 border rounded ${highlight ? "bg-blue-100" : ""}`}>
      <p>Topic {topic.topic_name}</p>
      <p>{topic.strength}</p>
      <p>{topic.suggested_time_minutes} mins</p>
    </div>
  );
}