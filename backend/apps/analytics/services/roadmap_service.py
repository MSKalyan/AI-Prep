from collections import defaultdict
from apps.analytics.services.adaptive_service import AdaptiveRoadmapService
from apps.roadmap.models import RoadmapTopic


class RoadmapService:

    @staticmethod
    def generate_adaptive_roadmap(user):

        roadmap = RoadmapTopic.objects.select_related("topic", "roadmap") \
            .filter(roadmap__user=user) \
            .order_by("week_number", "day_number", "id")

        if not roadmap.exists():
            return []

        # ✅ GROUP BY (week, day)
        day_map = defaultdict(list)

        for item in roadmap:
            key = (item.week_number, item.day_number)
            day_map[key].append(item)

        # ---------- PRIORITY ----------
        priority_topics = AdaptiveRoadmapService.generate_priority(user)

        weak_topics = [t for t in priority_topics if t["strength"] == "weak"]

        if not weak_topics:
            weak_topics = priority_topics[:3]

        used_revision_ids = set()
        result = []

        # ---------- BUILD PLAN ----------
        for (week, day) in sorted(day_map.keys()):

            topics_today = day_map[(week, day)]

            # ✅ REMOVE DUPLICATES
            seen = set()
            learn_topics = []

            for item in topics_today:
                if item.topic.id not in seen:
                    learn_topics.append({
                        "topic_id": item.topic.id,
                        "topic_name": item.topic.name
                    })
                    seen.add(item.topic.id)

            day_plan = {
                "week": week,   # ✅ include week
                "day": day,
                "learn_topics": learn_topics,
                "revisions": []
            }

            # ---------- REVISION ----------
            for topic in weak_topics:
                if topic["topic_id"] not in used_revision_ids:
                    day_plan["revisions"].append({
                        "topic_id": topic["topic_id"],
                        "topic_name": topic["topic_name"],
                        "priority": topic["priority"]
                    })

                    used_revision_ids.add(topic["topic_id"])
                    break

            result.append(day_plan)

        return result
    

    @staticmethod
    def get_today_plan(user):

        roadmap = RoadmapTopic.objects.select_related("topic", "roadmap") \
            .filter(roadmap__user=user) \
            .order_by("week_number", "day_number", "id")

        if not roadmap.exists():
            return {}

        # ---------- GROUP ----------
        from collections import defaultdict
        day_map = defaultdict(list)

        for item in roadmap:
            key = (item.week_number, item.day_number)
            day_map[key].append(item)

        # ---------- PICK TODAY ----------
        keys = sorted(day_map.keys())

        # simple: pick first incomplete day
        today_key = keys[0]  # later you can track progress

        week, day = today_key
        topics_today = day_map[today_key]

        # ---------- LEARN ----------
        seen = set()
        learn_topics = []

        for item in topics_today:
            if item.topic.id not in seen:
                learn_topics.append({
                    "topic_id": item.topic.id,
                    "topic_name": item.topic.name
                })
                seen.add(item.topic.id)

        # ---------- REVISION ----------
        priority_topics = AdaptiveRoadmapService.generate_priority(user)

        weak_topics = [t for t in priority_topics if t["strength"] == "weak"]

        revision = weak_topics[0] if weak_topics else None

        return {
            "week": week,
            "day": day,
            "learn_topics": learn_topics,
            "revision": revision
        }