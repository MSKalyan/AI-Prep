from apps.analytics.models import TopicPerformance


class AdaptiveRoadmapService:

    CONFIG = {
        "WEAK_MULTIPLIER": 1.0,
        "MODERATE_MULTIPLIER": 0.7,
        "STRONG_MULTIPLIER": 0.3,
        "INSUFFICIENT_MULTIPLIER": 0.2,
        "WEAK_BOOST": 1.0
    }

    @staticmethod
    def generate_priority(user):

        performances = TopicPerformance.objects.select_related("topic").filter(user=user)

        # ---------- NEW USER ----------
        if not performances.exists():
            from apps.roadmap.models import Topic

            topics = Topic.objects.all()

            results = []

            for topic in topics:
                weightage = getattr(topic, "weightage", 1.0)

                results.append({
                    "topic_id": topic.id,
                    "topic_name": topic.name,
                    "priority": round(weightage, 4),
                    "accuracy": 0.0,
                    "strength": "new",
                    "weightage": weightage
                })

            results.sort(key=lambda x: (-x["priority"], x["topic_id"]))
            return results

        # ---------- NORMAL FLOW ----------
        max_weight = max(p.topic.weightage for p in performances)

        results = []

        for perf in performances:
            topic = perf.topic
            accuracy = perf.accuracy
            attempts = perf.total_attempts
            strength = perf.strength

            weightage = topic.weightage or 1.0
            weightage_norm = weightage / max_weight if max_weight > 0 else 0

            weakness = 1 - accuracy

            if strength == "insufficient":
                priority = weightage_norm * AdaptiveRoadmapService.CONFIG["INSUFFICIENT_MULTIPLIER"]

            elif strength == "weak":
                priority = (
                    weakness * weightage_norm * AdaptiveRoadmapService.CONFIG["WEAK_MULTIPLIER"]
                    + AdaptiveRoadmapService.CONFIG["WEAK_BOOST"]
                )

            elif strength == "moderate":
                priority = weakness * weightage_norm * AdaptiveRoadmapService.CONFIG["MODERATE_MULTIPLIER"]

            else:
                priority = weakness * weightage_norm * AdaptiveRoadmapService.CONFIG["STRONG_MULTIPLIER"]

            results.append({
                "topic_id": topic.id,
                "topic_name": topic.name,
                "priority": round(priority, 4),
                "accuracy": round(accuracy, 2),
                "strength": strength,
                "weightage": weightage
            })

        results.sort(key=lambda x: (-x["priority"], x["topic_id"]))
        return results

    @staticmethod
    def get_revision_map(user):
        """
        Returns topic_id → adaptive metadata
        """

        priority_topics = AdaptiveRoadmapService.generate_priority(user)

        revision_map = {}

        for topic in priority_topics:
            revision_map[topic["topic_id"]] = {
                "topic_name": topic["topic_name"],
                "priority": topic["priority"],
                "strength": topic["strength"]
            }

        return revision_map
    
    @staticmethod
    def get_today_revision(user, limit=3):
        """
        Returns top weak topics NOT in today's learning topics
        """

        from apps.roadmap.models import RoadmapTopic

        # 1. Get priority topics
        priority_topics = AdaptiveRoadmapService.generate_priority(user)

        # 2. Get today's topics
        today_topics = RoadmapTopic.objects.filter(
            roadmap__user=user,
            roadmap__is_active=True
        ).values_list("topic_id", flat=True)

        today_topic_ids = set(today_topics)

        # 3. Filter weak topics NOT in today
        revision_candidates = [
            t for t in priority_topics
            if t["strength"] == "weak" and t["topic_id"] not in today_topic_ids
        ]

        # 4. Take top N
        return revision_candidates[:limit]