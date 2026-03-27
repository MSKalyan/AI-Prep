from apps.analytics.services.services import AttemptAggregationService
from apps.analytics.models import TopicPerformance
from apps.roadmap.models import Topic


class PerformanceService:

    @staticmethod
    def compute_and_store(user):
        """
        Reads aggregated topic data → computes metrics → stores in DB
        """

        aggregated_data = AttemptAggregationService.get_topic_wise_aggregation(user)

        if not aggregated_data:
            return []

        # ✅ STEP 1 — Extract all topic_ids ONCE
        topic_ids = [item["topic_id"] for item in aggregated_data]

        # ✅ STEP 2 — Fetch all topics in ONE query
        topics = Topic.objects.filter(id__in=topic_ids)

        # ✅ STEP 3 — Build lookup map
        topic_map = {t.id: t.name for t in topics}

        results = []

        # ✅ STEP 4 — Process each item
        for item in aggregated_data:
            topic_id = item["topic_id"]   # ✅ FIXED

            total_attempts = item["total_attempts"]
            correct_answers = item["correct_answers"]
            total_time = item["total_time"]

            # --- Safe calculations ---
            if total_attempts > 0:
                accuracy = correct_answers / total_attempts
                avg_time = total_time / total_attempts
            else:
                accuracy = 0.0
                avg_time = 0.0

            strength = PerformanceService.classify_topic(accuracy, total_attempts)

            # --- Persist (idempotent) ---
            TopicPerformance.objects.update_or_create(
                user=user,
                topic_id=topic_id,
                defaults={
                    "accuracy": accuracy,
                    "avg_time": avg_time,
                    "total_attempts": total_attempts,
                    "strength": strength
                }
            )

            # --- Response payload ---
            results.append({
                "topic_id": topic_id,
                "topic_name": topic_map.get(topic_id, ""),  # ✅ FIXED
                "accuracy": round(accuracy, 2),
                "avg_time": round(avg_time, 2),
                "total_attempts": total_attempts,
                "strength": strength
            })

        return results

    @staticmethod
    def classify_topic(accuracy, attempts):
        if attempts < 3:
            return "insufficient"
        elif accuracy < 0.4:
            return "weak"
        elif accuracy < 0.7:
            return "moderate"
        else:
            return "strong"