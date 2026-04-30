from django.core.management.base import BaseCommand

from apps.analytics.services.study_content_service import StudyContentService
from apps.roadmap.models import Topic


class Command(BaseCommand):
    help = "Pre-generate and cache study content for topics outside request handling."

    def add_arguments(self, parser):
        parser.add_argument(
            "--topic-id",
            type=int,
            default=None,
            help="Generate cache for a single topic id",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of topics to process when topic-id is not provided",
        )

    def handle(self, *args, **options):
        topic_id = options["topic_id"]
        limit = max(1, int(options["limit"]))

        queryset = Topic.objects.all().order_by("id")
        if topic_id:
            queryset = queryset.filter(id=topic_id)
        else:
            queryset = queryset[:limit]

        processed = 0
        for topic in queryset:
            StudyContentService._generate_and_cache(topic)
            processed += 1

        self.stdout.write(
            self.style.SUCCESS(f"Study content refresh completed for {processed} topic(s).")
        )
