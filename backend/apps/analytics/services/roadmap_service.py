from collections import defaultdict
from apps.analytics.services.adaptive_service import AdaptiveRoadmapService
from apps.roadmap.models import RoadmapTopic
class RoadmapService:
    @staticmethod
    def _get_user_roadmap(user):
        return RoadmapTopic.objects.select_related("topic", "roadmap") \
            .filter(roadmap__user=user) \
            .order_by("week_number", "day_number", "id")
    @staticmethod
    def _group_by_day(roadmap):
        day_map = defaultdict(list)
        for item in roadmap:
            key = (item.week_number, item.day_number)
            day_map[key].append(item)
        return day_map
    @staticmethod
    def _extract_learn_topics(items):
        seen = set()
        learn_topics = []
        for item in items:
            if item.topic.id not in seen:
                learn_topics.append({
                    "topic_id": item.topic.id,
                    "topic_name": item.topic.name
                })
                seen.add(item.topic.id)
        return learn_topics
    @staticmethod
    def _get_weak_topics(user):
        priority_topics = AdaptiveRoadmapService.generate_priority(user)
        weak = [t for t in priority_topics if t["strength"] == "weak"]
        return weak if weak else priority_topics[:3]
    @staticmethod
    def generate_adaptive_roadmap(user):
        roadmap = RoadmapService._get_user_roadmap(user)
        if not roadmap.exists():
            return []
        day_map = RoadmapService._group_by_day(roadmap)
        weak_topics = RoadmapService._get_weak_topics(user)
        used_revision_ids = set()
        result = []
        for (week, day) in sorted(day_map.keys()):
            topics_today = day_map[(week, day)]
            day_plan = {
                "week": week,
                "day": day,
                "learn_topics": RoadmapService._extract_learn_topics(topics_today),
                "revisions": []
            }
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
        roadmap = RoadmapService._get_user_roadmap(user)
        if not roadmap.exists():
            return {}
        day_map = RoadmapService._group_by_day(roadmap)
        today_key = min(day_map.keys())[0]
        week, day = today_key
        topics_today = day_map[today_key]
        weak_topics = RoadmapService._get_weak_topics(user)
        revision = weak_topics[0] if weak_topics else None
        return {
            "week": week,
            "day": day,
            "learn_topics": RoadmapService._extract_learn_topics(topics_today),
            "revision": revision
        }