from django.db import transaction
from apps.roadmap.models import Roadmap, RoadmapTopic, Exam, Topic
from apps.roadmap.services.pyq.time_distribution_service import TimeDistributionService
from apps.roadmap.services.pyq.weightage_service import WeightageService

class RoadmapService:

    @staticmethod
    @transaction.atomic
    def generate_deterministic_roadmap(user, exam_id, target_date, study_hours_per_day):
        # 1. Initialization
        exam = Exam.objects.get(id=exam_id)
        WeightageService.compute_weightage(exam)
        plan_result = TimeDistributionService.generate_plan(exam, target_date, study_hours_per_day)

        # 2. Hard Reset
        Roadmap.objects.filter(user=user, is_active=True).delete() 
        
        roadmap = Roadmap.objects.create(
            user=user, 
            exam=exam, 
            target_date=target_date,
            total_weeks=plan_result["total_weeks"], 
            is_active=True
        )

        global_fallback = Topic.objects.filter(subject__exam=exam).first()
        daily_limit = float(study_hours_per_day)

        # 3. Iterate through weeks
        for week_data in plan_result["plan"]:
            w_num = week_data["week_number"]
            
            # --- DAY 6: REVISION (AMBER) ---
            rev_topic = week_data["items"][-1]["topic"] if week_data["items"] else global_fallback
            RoadmapTopic.objects.create(
                roadmap=roadmap, week_number=w_num, day_number=6,
                topic=rev_topic, estimated_hours=daily_limit,
                phase="revision", priority=1
            )

            # --- DAY 7: MOCK TEST (RED) ---
            mock_topic = week_data["items"][0]["topic"] if week_data["items"] else global_fallback
            RoadmapTopic.objects.create(
                roadmap=roadmap, week_number=w_num, day_number=7,
                topic=mock_topic, estimated_hours=daily_limit,
                phase="practice", priority=1
            )

            # --- DAYS 1-5: PACKED STUDY (BLUE) ---
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
                            phase="study"
                        )
                    
                    topic_h -= allocated
                    day_rem_h -= allocated

                    # If day is full (or near full), move to next day
                    if day_rem_h <= 0.1:
                        curr_day += 1
                        day_rem_h = daily_limit

        return roadmap