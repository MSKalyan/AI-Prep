import math
from apps.analytics.models import TopicPerformance


class AdaptiveRoadmapService:

    @staticmethod
    def generate_priority(user):

        performances = TopicPerformance.objects.select_related("topic").filter(user=user)

        if not performances.exists():
            return []

        results = []

        for perf in performances:
            topic = perf.topic
            accuracy = perf.accuracy
            attempts = perf.total_attempts
            strength = perf.strength

            weightage = getattr(topic, "weightage", 1.0)
            weightage = min(weightage, 5)
            # --- Priority Calculation ---
            if strength == "insufficient":
                priority = weightage * 0.1   # very low influence
            elif strength == "weak":
                priority = (1 - accuracy) * weightage * math.log(attempts + 1)
            elif strength == "moderate":
                priority = (1 - accuracy) * weightage * 0.7
            else:  # strong
                priority = (1 - accuracy) * weightage * 0.3
          
            results.append({
                "topic_id": topic.id,
                "topic_name":topic.name,
                "priority": round(priority, 4),
                "accuracy": round(accuracy, 2),
                "strength": strength,
                "weightage": weightage
            })

        # --- Sort (MOST IMPORTANT) ---
        results.sort(key=lambda x: x["priority"], reverse=True)

        return results