from apps.analytics.models import TopicPerformance
from apps.roadmap.models import Topic, RoadmapTopic


class AdaptiveRoadmapService:
    CONFIG = {
        "WEAK_MULTIPLIER": 1.0,
        "MODERATE_MULTIPLIER": 0.7,
        "STRONG_MULTIPLIER": 0.3,
        "INSUFFICIENT_MULTIPLIER": 0.2,
        "WEAK_BOOST": 1.0,
    }

    @staticmethod
    def generate_priority(user):
        performances = TopicPerformance.objects.select_related("topic").filter(user=user)

        if not performances.exists():
            return AdaptiveRoadmapService._default_priorities()

        max_weight = max(p.topic.weightage for p in performances)

        results = [
            AdaptiveRoadmapService._build_priority_item(perf, max_weight)
            for perf in performances
        ]

        return AdaptiveRoadmapService._sort_results(results)

    @staticmethod
    def _default_priorities():
        topics = Topic.objects.all()

        results = [
            {
                "topic_id": topic.id,
                "topic_name": topic.name,
                "priority": round(getattr(topic, "weightage", 1.0), 4),
                "accuracy": 0.0,
                "strength": "new",
                "weightage": getattr(topic, "weightage", 1.0),
            }
            for topic in topics
        ]

        return AdaptiveRoadmapService._sort_results(results)

    @staticmethod
    def _calculate_priority(accuracy, strength, weightage_norm):
        config = AdaptiveRoadmapService.CONFIG
        weakness = 1 - accuracy

        if strength == "insufficient":
            return weightage_norm * config["INSUFFICIENT_MULTIPLIER"]

        if strength == "weak":
            return (
                weakness * weightage_norm * config["WEAK_MULTIPLIER"]
                + config["WEAK_BOOST"]
            )

        if strength == "moderate":
            return weakness * weightage_norm * config["MODERATE_MULTIPLIER"]

        return weakness * weightage_norm * config["STRONG_MULTIPLIER"]

    @staticmethod
    def _build_priority_item(perf, max_weight):
        topic = perf.topic
        weightage = topic.weightage or 1.0
        weightage_norm = weightage / max_weight if max_weight > 0 else 0

        priority = AdaptiveRoadmapService._calculate_priority(
            perf.accuracy, perf.strength, weightage_norm
        )

        return {
            "topic_id": topic.id,
            "topic_name": topic.name,
            "priority": round(priority, 4),
            "accuracy": round(perf.accuracy, 2),
            "strength": perf.strength,
            "weightage": weightage,
        }

    @staticmethod
    def _sort_results(results):
        return sorted(results, key=lambda x: (-x["priority"], x["topic_id"]))

    @staticmethod
    def get_revision_map(user):
        """
        Returns topic_id -> adaptive metadata
        """

        priority_topics = AdaptiveRoadmapService.generate_priority(user)

        revision_map = {}

        for topic in priority_topics:
            revision_map[topic["topic_id"]] = {
                "topic_name": topic["topic_name"],
                "priority": topic["priority"],
                "strength": topic["strength"],
            }

        return revision_map

    @staticmethod
    def get_today_revision(user, limit=3):
        """
        Returns top weak topics NOT in today's learning topics
        """

        priority_topics = AdaptiveRoadmapService.generate_priority(user)

        # 2. Get today's topics
        today_topics = RoadmapTopic.objects.filter(
            roadmap__user=user, roadmap__is_active=True
        ).values_list("topic_id", flat=True)

        today_topic_ids = set(today_topics)

        # 3. Filter weak topics NOT in today
        revision_candidates = [
            t
            for t in priority_topics
            if t["strength"] == "weak" and t["topic_id"] not in today_topic_ids
        ]

        # 4. Take top N
        return revision_candidates[:limit]