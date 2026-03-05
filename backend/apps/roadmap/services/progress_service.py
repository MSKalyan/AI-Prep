from apps.roadmap.models import RoadmapTopic


class ProgressService:

    @staticmethod
    def get_week_progress(roadmap_id, week_number):

        topics = RoadmapTopic.objects.filter(
            roadmap_id=roadmap_id,
            week_number=week_number
        )

        total_topics = topics.count()
        completed_topics = topics.filter(is_completed=True).count()

        progress = 0
        if total_topics > 0:
            progress = round((completed_topics / total_topics) * 100)

        return {
            "week": week_number,
            "total_topics": total_topics,
            "completed_topics": completed_topics,
            "progress": progress
        }

    @staticmethod
    def get_overall_progress(roadmap_id):

        topics = RoadmapTopic.objects.filter(
            roadmap_id=roadmap_id
        )

        total_topics = topics.count()
        completed_topics = topics.filter(is_completed=True).count()

        progress = 0
        if total_topics > 0:
            progress = round((completed_topics / total_topics) * 100)

        return {
            "roadmap_id": roadmap_id,
            "total_topics": total_topics,
            "completed_topics": completed_topics,
            "progress": progress
        }