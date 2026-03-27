from .adaptive_service import AdaptiveRoadmapService


class RoadmapService:

    @staticmethod
    def generate_adaptive_roadmap(user):

        ranked_topics = AdaptiveRoadmapService.generate_priority(user)

        if not ranked_topics:
            return []

        # --- Normalize priorities ---
        total_priority = sum(t["priority"] for t in ranked_topics if t["priority"] > 0)

        roadmap = []

        for topic in ranked_topics:

            priority = topic["priority"]

            if total_priority > 0:
                time_alloc = max((priority / total_priority) * 100 ,5) # total 100 mins
            else:
                time_alloc = 5  # fallback

            roadmap.append({
                "topic_id": topic["topic_id"],
                "priority": priority,
                "suggested_time_minutes": round(time_alloc, 2),
                "strength": topic["strength"]
            })

        return roadmap