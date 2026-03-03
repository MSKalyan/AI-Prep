"use client";

interface Topic {
  id: number;
  week_number: number;
  subject_name: string;
  topic_name: string;
  estimated_hours: number;
  priority: number;
  is_completed: boolean;
  phase: string;
}

interface Roadmap {
  id: number;
  exam?: {
    id: number;
    name: string;
  };
  target_date: string;
  difficulty_level: string;
  total_weeks: number;
  description?: string;
  topics: Topic[];
}

interface Props {
  roadmap: Roadmap;
}

export default function RoadmapPreview({ roadmap }: Props) {

  // -------------------------
  // Group topics by week
  // -------------------------
  const groupedByWeek = roadmap.topics.reduce((acc: any, topic: Topic) => {
    if (!acc[topic.week_number]) {
      acc[topic.week_number] = [];
    }
    acc[topic.week_number].push(topic);
    return acc;
  }, {});

  const sortedWeeks = Object.keys(groupedByWeek)
    .map(Number)
    .sort((a, b) => a - b);

  return (
    <div className="space-y-6">

      {/* =========================
          ROADMAP HEADER
      ========================= */}
      <div className="rounded-lg border bg-white p-6 shadow-sm">

        <h2 className="text-2xl font-semibold text-gray-800">
          {roadmap.exam?.name ?? "Study Roadmap"}
        </h2>

        <div className="mt-2 text-sm text-gray-600 space-y-1">
          <p><strong>Target Date:</strong> {roadmap.target_date}</p>
          <p><strong>Total Weeks:</strong> {roadmap.total_weeks}</p>
        </div>

        {roadmap.description && (
          <p className="mt-4 text-sm text-gray-700">
            {roadmap.description}
          </p>
        )}
      </div>

      {/* =========================
          WEEK CARDS
      ========================= */}

      {sortedWeeks.length === 0 && (
        <p className="text-sm text-gray-600">
          No topics found for this roadmap.
        </p>
      )}

      {sortedWeeks.map((weekNumber) => {

        const weekTopics = groupedByWeek[weekNumber];

        const totalWeekHours = weekTopics.reduce(
          (sum: number, t: Topic) => sum + t.estimated_hours,
          0
        );

        return (
          <div
            key={weekNumber}
            className="rounded-lg border bg-white p-5 shadow-sm"
          >

            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800">
                Week {weekNumber}
              </h3>

             <span
  className={`text-xs px-2 py-1 rounded ${
    weekTopics[0]?.phase === "coverage"
      ? "bg-blue-100 text-blue-700"
      : weekTopics[0]?.phase === "practice"
      ? "bg-yellow-100 text-yellow-700"
      : "bg-purple-100 text-purple-700"
  }`}
>
  {weekTopics[0]?.phase?.toUpperCase()}
</span>
            </div>

            <div className="space-y-2">
              {weekTopics.map((topic: Topic) => (
                <div
                  key={topic.id}
                  className="flex items-center justify-between text-sm border-b pb-1 last:border-none"
                >
                  <div>
                    <span className="text-gray-800">
                    {topic.subject_name} → {topic.topic_name}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-gray-500 text-xs">
                    <span>{topic.estimated_hours} hrs</span>
                    <span
                      className={`px-2 py-0.5 rounded ${
                        topic.is_completed
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {topic.is_completed ? "Done" : "Pending"}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 text-xs text-gray-500">
              Total Hours: {totalWeekHours}
            </div>

          </div>
        );
      })}

    </div>
  );
}