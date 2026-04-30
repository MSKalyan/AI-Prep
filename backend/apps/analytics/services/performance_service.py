from apps.analytics.services.services import AttemptAggregationService
from apps.analytics.models import TopicPerformance
from apps.roadmap.models import Topic


class PerformanceService:

    @staticmethod
    def compute_and_store(user):
        aggregated_data = AttemptAggregationService.get_topic_wise_aggregation(user)

        if not aggregated_data:
            return []

        topic_map = PerformanceService._get_topic_map(aggregated_data)

        results = [
            PerformanceService._process_item(user, item, topic_map)
            for item in aggregated_data
        ]

        return results
    @staticmethod
    def _get_topic_map(aggregated_data):
        topic_ids = [item["topic_id"] for item in aggregated_data]

        topics = Topic.objects.filter(id__in=topic_ids)

        return {
            t.id: {"name": t.name, "weightage": t.weightage}
            for t in topics
        }
    @staticmethod
    def _process_item(user, item, topic_map):
        topic_id = item["topic_id"]

        metrics = PerformanceService._compute_metrics(item)
        strength = PerformanceService.classify_topic(
            metrics["accuracy"], metrics["total_attempts"]
        )

        PerformanceService._store_performance(user, topic_id, metrics, strength)

        topic_data = topic_map.get(topic_id, {"name": "", "weightage": 1.0})

        return PerformanceService._build_result(
            topic_id, topic_data, metrics, strength
        )
    @staticmethod
    def _compute_metrics(item):
        total_attempts = item["total_attempts"]
        correct_answers = item["correct_answers"]
        total_time = item["total_time"]

        if total_attempts > 0:
            return {
                "accuracy": correct_answers / total_attempts,
                "avg_time": total_time / total_attempts,
                "total_attempts": total_attempts,
            }

        return {
            "accuracy": 0.0,
            "avg_time": 0.0,
            "total_attempts": total_attempts,
        }
    @staticmethod
    def _store_performance(user, topic_id, metrics, strength):
        TopicPerformance.objects.update_or_create(
            user=user,
            topic_id=topic_id,
            defaults={
                "accuracy": metrics["accuracy"],
                "avg_time": metrics["avg_time"],
                "total_attempts": metrics["total_attempts"],
                "strength": strength,
            },
        )
    @staticmethod
    def _build_result(topic_id, topic_data, metrics, strength):
        return {
            "topic_id": topic_id,
            "topic_name": topic_data["name"],
            "accuracy": round(metrics["accuracy"], 2),
            "avg_time": round(metrics["avg_time"], 2),
            "total_attempts": metrics["total_attempts"],
            "strength": strength,
            "weightage": topic_data["weightage"],
        }
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