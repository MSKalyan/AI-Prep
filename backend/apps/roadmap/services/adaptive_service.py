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
  