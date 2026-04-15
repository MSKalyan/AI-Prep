from django.db import transaction
from apps.roadmap.models import Roadmap, RoadmapTopic, Exam, Topic
from apps.roadmap.services.pyq.time_distribution_service import TimeDistributionService
from apps.roadmap.services.pyq.weightage_service import WeightageService
from apps.analytics.services.adaptive_service import AdaptiveRoadmapService


class RoadmapService:
    @staticmethod
    @transaction.atomic
    def generate_deterministic_roadmap(user, exam_id, target_date, study_hours_per_day):
        exam = Exam.objects.get(id=exam_id)
        WeightageService.compute_weightage(exam)
        plan = TimeDistributionService.generate_plan(
            exam, target_date, study_hours_per_day
        )
        return RoadmapService._create_roadmap(
            user, exam, target_date, plan, study_hours_per_day
        )

    @staticmethod
    def _create_roadmap(user, exam, target_date, plan, study_hours_per_day):
        Roadmap.objects.filter(user=user, is_active=True).update(is_active=False)
        roadmap = Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=target_date,
            total_weeks=plan["total_weeks"],
            is_active=True,
        )
        RoadmapService._add_topics(roadmap, exam, plan, study_hours_per_day)
        return roadmap

    @staticmethod
    def _add_topics(roadmap, exam, plan, study_hours_per_day):
        fallback = Topic.objects.filter(subject__exam=exam).first()
        daily_limit = float(study_hours_per_day)
        for week_data in plan["plan"]:
            RoadmapService._create_week_topics(
                roadmap, week_data, fallback, daily_limit
            )

    @staticmethod
    def _create_week_topics(roadmap, week_data, global_fallback, daily_limit):
        w_num = week_data["week_number"]

        rev_topic = (
            week_data["items"][-1]["topic"] if week_data["items"] else global_fallback
        )
        RoadmapTopic.objects.create(
            roadmap=roadmap,
            week_number=w_num,
            day_number=6,
            topic=rev_topic,
            estimated_hours=daily_limit,
            phase="revision",
            priority=1,
        )

        mock_topic = (
            week_data["items"][0]["topic"] if week_data["items"] else global_fallback
        )
        RoadmapTopic.objects.create(
            roadmap=roadmap,
            week_number=w_num,
            day_number=7,
            topic=mock_topic,
            estimated_hours=daily_limit,
            phase="practice",
            priority=1,
        )

        curr_day = 1
        day_rem_h = daily_limit

        for item in week_data["items"]:
            topic_h = float(item["hours"])

            while topic_h > 0.1 and curr_day <= 5:
                allocated = min(topic_h, day_rem_h)

                if allocated > 0.1:
                    RoadmapTopic.objects.create(
                        roadmap=roadmap,
                        week_number=w_num,
                        day_number=curr_day,
                        topic=item["topic"],
                        estimated_hours=round(allocated, 1),
                        phase="study",
                    )

                topic_h -= allocated
                day_rem_h -= allocated

                if day_rem_h <= 0.1:
                    curr_day += 1
                    day_rem_h = daily_limit

    @staticmethod
    def get_user_roadmap(user):
        from collections import defaultdict

        roadmap = (
            RoadmapTopic.objects.select_related("topic", "roadmap")
            .filter(roadmap__user=user, roadmap__is_active=True)
            .order_by("week_number", "day_number", "id")
        )

        if not roadmap.exists():
            return []

        revision_map = AdaptiveRoadmapService.get_revision_map(user)
        grouped = defaultdict(list)

        for item in roadmap:
            key = (item.week_number, item.day_number)
            grouped[key].append(item)

        return RoadmapService._build_roadmap_result(grouped, revision_map)

    @staticmethod
    def _build_roadmap_result(grouped, revision_map):
        result = []
        for week, day in sorted(grouped.keys()):
            topics = [
                RoadmapService._build_topic_item(item, revision_map)
                for item in grouped[(week, day)]
            ]
            topics.sort(
                key=lambda t: (
                    not t["adaptive"]["is_revision"],
                    -t["adaptive"]["priority"],
                )
            )
            result.append({"week": week, "day": day, "topics": topics})
        return result

    @staticmethod
    def _build_topic_item(item, revision_map):
        adaptive = revision_map.get(item.topic.id)
        return {
            "topic_id": item.topic.id,
            "topic_name": item.topic.name,
            "estimated_hours": item.estimated_hours,
            "phase": item.phase,
            "adaptive": {
                "strength": adaptive["strength"] if adaptive else "unknown",
                "priority": adaptive["priority"] if adaptive else 0,
                "is_revision": (adaptive["strength"] == "weak" if adaptive else False),
            },
        }
