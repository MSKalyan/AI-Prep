from datetime import date

from apps.roadmap.models import Exam, Subject, Topic

def save_syllabus(exam_name, syllabus):

    exam, _ = Exam.objects.get_or_create(name=exam_name, defaults={
        "exam_date": date(2027, 2, 1),  # approximate GATE month
        "category": "Engineering",
        "total_marks": 100,
    })

    for subject_index, (subject_name, topics) in enumerate(syllabus.items()):
        print("SUBJECT:", subject_name, len(subject_name))
        subject, _ = Subject.objects.get_or_create(
            exam=exam,
            name=subject_name,
            order=subject_index
        )

        for topic_index, topic_name in enumerate(topics):

            Topic.objects.get_or_create(
                subject=subject,
                name=topic_name,
                order=topic_index
            )