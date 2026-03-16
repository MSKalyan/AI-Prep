from datetime import date

from apps.roadmap.models import Exam, Subject, Topic, Subtopic


def save_syllabus(exam_name, syllabus):

    exam, _ = Exam.objects.get_or_create(
        name=exam_name,
        defaults={
            "exam_date": date(2027, 2, 1),   # approximate GATE month
            "category": "Engineering",
            "total_marks": 100,
        }
    )

    for subject_index, subject_data in enumerate(syllabus):

        subject_name = subject_data["subject"]

        print("SUBJECT:", subject_name)

        subject, _ = Subject.objects.get_or_create(
            exam=exam,
            name=subject_name,
            defaults={"order": subject_index}
        )

        for topic_index, topic_data in enumerate(subject_data["topics"]):

            topic_name = topic_data["topic"]

            topic, _ = Topic.objects.get_or_create(
                subject=subject,
                name=topic_name,
                defaults={"order": topic_index}
            )

            for sub_index, subtopic_name in enumerate(topic_data["subtopics"]):

                Subtopic.objects.get_or_create(
                    topic=topic,
                    name=subtopic_name,
                    defaults={"order": sub_index}
                )