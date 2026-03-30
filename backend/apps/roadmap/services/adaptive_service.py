from collections import defaultdict
from apps.mocktest.models import Answer


class AdaptiveRoadmapService:

    @staticmethod
    def compute_topic_accuracy(user, roadmap):

        answers = Answer.objects.filter(
            attempt__user=user,
            attempt__mock_test__roadmap=roadmap
        ).select_related("question__topic_obj")

        topic_stats = defaultdict(lambda: {"correct": 0, "total": 0})

        for ans in answers:
            topic = ans.question.topic_obj
            if not topic:
                continue

            topic_stats[topic]["total"] += 1
            if ans.is_correct:
                topic_stats[topic]["correct"] += 1

        topic_accuracy = {}

        for topic, data in topic_stats.items():
            total = data["total"]
            correct = data["correct"]
            accuracy = (correct / total) * 100 if total > 0 else 0
            topic_accuracy[topic] = accuracy

        return topic_accuracy
  
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