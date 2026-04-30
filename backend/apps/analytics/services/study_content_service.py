import os
import requests
import logging
from datetime import timedelta

from django.utils import timezone

from apps.analytics.models import StudyContentCache
from apps.roadmap.models import Topic
from groq import Groq
from common.utils.retry_utils import safe_get, safe_llm_call

logger = logging.getLogger(__name__)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
REQUEST_TIMEOUT_SECONDS = 10

class StudyContentService:
    @staticmethod
    def get_client():
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None
        return Groq(api_key=api_key)
    @staticmethod
    def generate_queries(topic_name):
        client = StudyContentService.get_client()

        if not client:
            return StudyContentService._default_queries(topic_name)

        try:
            response = StudyContentService._call_llm_for_queries(client, topic_name)
            return StudyContentService._parse_queries(response)

        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            logger.error("Failed to generate study content queries via LLM", exc_info=True)
            return StudyContentService._default_queries(topic_name)
    @staticmethod
    def _default_queries(topic_name):
        return [
            f"{topic_name} GATE tutorial English",
            f"{topic_name} GATE exam problems English",
            f"{topic_name} GATE interview questions English"
        ]

    @staticmethod
    def _call_llm_for_queries(client, topic_name):
        prompt = f"""
        Generate exactly only 3 high-quality YouTube search queries for GATE exam preparation on:
        {topic_name}
        """
        return safe_llm_call(
            client,
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}]
        )

    @staticmethod
    def _parse_queries(response):
        text = response.choices[0].message.content
        return [
            line.strip("- ").strip()
            for line in text.split("\n")
            if line.strip()
        ][:3]
    @staticmethod
    def generate_description(topic_name):
        client = StudyContentService.get_client()

        if not client:
            return StudyContentService._default_description(topic_name)

        prompt = f"""
        Explain {topic_name} in simple terms for students preparing for exams.
        Keep it short (5-6 lines).
        """
        try:
            res = safe_llm_call(
                client,
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            return res.choices[0].message.content.strip()

        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            logger.error("Failed to generate topic description via LLM", exc_info=True)
            return StudyContentService._default_description(topic_name)
    @staticmethod
    def _default_description(topic_name):
        return (
            f"{topic_name} is an important concept. Focus on understanding "
            "fundamentals and solving problems."
        )
    @staticmethod
    def fetch_youtube_videos(queries):
        if not YOUTUBE_API_KEY:
            return []
        videos = []
        preferred_langs = ["English", "Hindi"]
        for query in queries:
            query_videos = StudyContentService._fetch_videos_for_query(query, preferred_langs)
            videos.extend(query_videos)
            if len(videos) >= 3:
                break
        return list(dict.fromkeys(videos))[:3]

    @staticmethod
    def _fetch_videos_for_query(query, preferred_langs):
        videos = []

        for lang in preferred_langs:
            try:
                videos.extend(
                    StudyContentService._fetch_videos_for_language(query, lang)
                )
            except requests.RequestException:
                logger.warning("YouTube API request failed", exc_info=True)
            except (KeyError, TypeError, ValueError):
                logger.warning("Unexpected YouTube API payload", exc_info=True)

        return videos
    @staticmethod
    def _fetch_videos_for_language(query, lang):
        params = StudyContentService._build_youtube_params(query, lang)

        res = safe_get(
            "https://www.googleapis.com/youtube/v3/search",
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS
        )

        return StudyContentService._extract_videos(res.json())
    @staticmethod
    def _build_youtube_params(query, lang):
        return {
            "part": "snippet",
            "q": f"{query} {lang}",
            "key": YOUTUBE_API_KEY,
            "maxResults": 5,
            "type": "video",
            "videoDuration": "medium",
            "safeSearch": "strict"
        }
    @staticmethod
    def _extract_videos(data):
        videos = []

        for item in data.get("items", []):
            try:
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                channel = item["snippet"]["channelTitle"]

                if StudyContentService.is_good_video(title, channel):
                    videos.append(f"https://www.youtube.com/watch?v={video_id}")

            except (KeyError, TypeError):
                continue

        return videos
    @staticmethod
    def is_good_video(title, channel_title=""):
        bad_keywords = ["shorts", "trailer", "funny", "meme", "song", "lyrics", "comedy", "bollywood", "tollywood"]
        title_lower = title.lower()
        if any(word in title_lower for word in bad_keywords):
            return False
        unwanted_langs = ["tamil", "தமிழ்", "malayalam", "മലയാളം", "kannada", "ಕನ್ನಡ", "bengali", "বাংলা", "punjabi", " Gujarati", "marathi"]
        if any(lang in title_lower for lang in unwanted_langs):
            return False
        channel_lower = channel_title.lower()
        if any(lang in channel_lower for lang in unwanted_langs):
            return False

        return True

    @staticmethod
    def get_study_content(topic_name):
        if not topic_name:
            return None

        topic = Topic.objects.filter(name__iexact=str(topic_name).strip()).first()
        if not topic:
            return None
        cached = StudyContentService._get_cached_content(topic)
        if cached:
            return cached
        StudyContentService._enqueue_generation(topic.id)
        return StudyContentService._build_pending_content(topic)

    @staticmethod
    def _enqueue_generation(topic_id):
        try:
            from apps.analytics.tasks import generate_topic_study_content
            generate_topic_study_content.delay(topic_id)
        except Exception:
            logger.warning("Unable to enqueue study content generation task", exc_info=True)

    @staticmethod
    def _build_pending_content(topic):
        return {
            "topic_id": topic.id,
            "topic_name": topic.name,
            "description": StudyContentService._default_description(topic.name),
            "youtube_links": [],
        }

    @staticmethod
    def _get_cached_content(topic):
        """Check if valid cached content exists."""
        cached = StudyContentCache.objects.filter(topic=topic).first()
        if not cached or not cached.youtube_links:
            return None
        if (timezone.now() - cached.created_at) < timedelta(days=7):
            return {
                "topic_id": topic.id,
                "topic_name": topic.name,
                "description": cached.description,
                "youtube_links": cached.youtube_links
            }
        return None

    @staticmethod
    def _generate_and_cache(topic):
        topic_name = topic.name

        queries = StudyContentService.generate_queries(topic_name)
        videos = StudyContentService.fetch_youtube_videos(queries)
        description = StudyContentService.generate_description(topic_name)

        StudyContentService._save_cache(topic, description, videos)

        return {
            "topic_id": topic.id,
            "topic_name": topic_name,
            "description": description,
            "youtube_links": videos
        }
    @staticmethod
    def _save_cache(topic, description, videos):
        if not videos:
            return

        StudyContentCache.objects.update_or_create(
            topic=topic,
            defaults={
                "description": description,
                "youtube_links": videos
            }
        )
