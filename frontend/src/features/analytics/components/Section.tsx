import { TopicPerformance } from "../services/analytics.service";

export default function Section({
  title,
  data,
  emptyText,
}: {
  title: string;
  data: TopicPerformance[];
  emptyText: string;
}) {
  return (
    <div>
      <h2 className="text-base sm:text-lg md:text-xl font-semibold mb-4">
        {title}
      </h2>

      {data.length === 0 ? (
        <p className="text-xs sm:text-sm text-gray-500">{emptyText}</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {data.map((t) => (
            <div
              key={t.topic_id}
              className="border border-gray-200 rounded-2xl p-4 sm:p-5 hover:shadow-md transition"
            >
              <p className="font-medium text-sm sm:text-base mb-2">
                {t.topic_name || `Topic ${t.topic_id}`}
              </p>

              <div className="space-y-1 text-xs sm:text-sm text-gray-600">
                <p>Accuracy: {(t.accuracy * 100).toFixed(1)}%</p>
                <p>Avg Time: {t.avg_time}s</p>
                <p>Attempts: {t.total_attempts}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
