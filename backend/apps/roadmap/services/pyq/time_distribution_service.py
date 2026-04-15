from datetime import datetime
from apps.roadmap.models import Topic
from collections import defaultdict, deque


class TimeDistributionService:
    @staticmethod
    def generate_plan(exam, target_date, study_hours_per_day):
        today = datetime.now().date()
        total_weeks = max(1, (target_date - today).days // 7)
        all_topics = list(
            Topic.objects.filter(subject__exam=exam).order_by("-weightage")
        )

        if not all_topics:
            return {"total_weeks": total_weeks, "plan": []}

        subj_map = TimeDistributionService._group_topics_by_subject(all_topics)
        weekly_study_h = float(study_hours_per_day) * 5

        return TimeDistributionService._build_plan(
            total_weeks, subj_map, weekly_study_h
        )

    @staticmethod
    def _group_topics_by_subject(topics):
        from collections import deque

        subj_map = defaultdict(deque)
        for t in topics:
            s_id = t.subject_id if t.subject_id else 0
            subj_map[s_id].append(t)
        return subj_map

    @staticmethod
    def _build_plan(total_weeks, subj_map, weekly_study_h):
        subj_ids = list(subj_map.keys())
        plan = []

        for w in range(1, total_weeks + 1):
            week_items = TimeDistributionService._allocate_interleaved_subjects(
                w, subj_map, subj_ids, weekly_study_h
            )
            week_items = TimeDistributionService._backfill_remaining_hours(
                week_items, subj_map, subj_ids
            )
            plan.append({"week_number": w, "items": week_items})

        return {"total_weeks": total_weeks, "plan": plan}

    @staticmethod
    def _allocate_interleaved_subjects(week_num, subj_map, subj_ids, weekly_study_h):
        week_items = []

        s1_idx = (week_num - 1) % len(subj_ids)
        s2_idx = week_num % len(subj_ids)
        active_ids = [subj_ids[s1_idx]]
        if len(subj_ids) > 1:
            active_ids.append(subj_ids[s2_idx])

        for s_id in active_ids:
            q = subj_map[s_id]
            target_h = weekly_study_h / len(active_ids)
            items, _ = TimeDistributionService._allocate_from_topic(q, target_h)
            week_items.extend(items)

        return week_items

    @staticmethod
    def _allocate_from_topic(queue, target_h):
        week_items = []
        current_sub_h = 0
        while current_sub_h < target_h and queue:
            topic = queue.popleft()
            h = max(2.0, min(8.0, 2.0 + (float(topic.weightage or 0) * 0.8)))
            h = min(h, target_h - current_sub_h)
            if h >= 0.5:
                week_items.append({"topic": topic, "hours": round(h, 1)})
                current_sub_h += h
        return week_items, current_sub_h

    @staticmethod
    def _backfill_remaining_hours(week_items, subj_map, subj_ids):
        rem_h = sum(item["hours"] for item in week_items)
        if rem_h > 0.5:
            for s_id in subj_ids:
                q = subj_map[s_id]
                while rem_h > 0.5 and q:
                    topic = q.popleft()
                    h = min(rem_h, 4.0)
                    week_items.append({"topic": topic, "hours": round(h, 1)})
                    rem_h -= h
        return week_items


class DayDistributionService:
    @staticmethod
    def distribute_week(week_items, daily_limit):
        """
        Takes the packed week_items and distributes them into Days 1-5.
        Day 6 and 7 are reserved for Revision/Mock in RoadmapService.
        """
        days = []
        current_day = 1
        remaining_day_hours = float(daily_limit)

        for item in week_items:
            topic = item["topic"]
            hours = float(item["hours"])
            hours = round(hours, 2)
            remaining_day_hours = round(remaining_day_hours, 2)
            while hours > 0:
                if current_day > 5:  # Study only 5 days
                    break

                allocate = round(min(hours, remaining_day_hours), 2)

                if allocate > 0:
                    days.append(
                        {
                            "day": current_day,
                            "topic": topic,
                            "hours": round(allocate, 1),
                        }
                    )

                hours -= allocate
                remaining_day_hours -= allocate

                # Move to next day if this one is full
                if remaining_day_hours <= 0.1:
                    current_day += 1
                    remaining_day_hours = float(daily_limit)

        return days
