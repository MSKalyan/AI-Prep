from celery import shared_task

from apps.analytics.services.study_content_service import StudyContentService
from apps.roadmap.models import Topic


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def generate_topic_study_content(self, topic_id: int):
    topic = Topic.objects.filter(id=topic_id).first()
    if not topic:
        return None
    return StudyContentService._generate_and_cache(topic)
