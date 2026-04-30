import os
import httpx
import logging
import re
from datetime import timedelta
from asgiref.sync import async_to_sync

from django.utils import timezone
from django.conf import settings

from apps.analytics.models import StudyContentCache
from apps.roadmap.models import Topic
from groq import Groq
from common.utils.retry_utils import safe_get_async, safe_llm_call

logger = logging.getLogger(__name__)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
REQUEST_TIMEOUT_SECONDS = 10
STUDY_CONTENT_LLM_MODEL = os.getenv("STUDY_CONTENT_LLM_MODEL", settings.LLM_MODEL)

class StudyContentService:
    _STOPWORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
        "in", "into", "is", "it", "of", "on", "or", "that", "the", "to", "what",
        "when", "where", "which", "with", "without", "using", "use", "vs"
    }
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
        base = str(topic_name).strip()
        return [
            f"\"{base}\" GATE CS full tutorial concepts and PYQs English",
            f"\"{base}\" GATE previous year questions solved English",
            f"\"{base}\" GATE exam tricks mistakes and practice questions English"
        ]

    @staticmethod
    def _call_llm_for_queries(client, topic_name):
        prompt = f"""
        Generate exactly only 3 high-quality YouTube search queries for GATE exam preparation on:
        {topic_name}
        """
        return safe_llm_call(
            client,
            model=STUDY_CONTENT_LLM_MODEL,
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
                model=STUDY_CONTENT_LLM_MODEL,
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
        return async_to_sync(StudyContentService.fetch_youtube_videos_async)(queries)

    @staticmethod
    async def fetch_youtube_videos_async(queries):
        if not YOUTUBE_API_KEY:
            return await StudyContentService._scrape_youtube_video_links_async(queries)
        videos = []
        preferred_langs = ["English", "Hindi"]
        for query in queries:
            query_videos = await StudyContentService._fetch_videos_for_query_async(query, preferred_langs)
            videos.extend(query_videos)
            if len(videos) >= 3:
                break
        deduped = list(dict.fromkeys(videos))[:3]
        if deduped:
            return deduped
        # If API key exists but requests fail (e.g. 403 quota/restrictions), degrade gracefully.
        return await StudyContentService._scrape_youtube_video_links_async(queries)

    @staticmethod
    async def _scrape_youtube_video_links_async(queries):
        links = []
        for query in queries:
            try:
                search_url = "https://www.youtube.com/results"
                res = await safe_get_async(
                    search_url,
                    params={"search_query": query},
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", res.text or "")
                for video_id in video_ids:
                    link = f"https://www.youtube.com/watch?v={video_id}"
                    if link not in links:
                        links.append(link)
                    if len(links) >= 3:
                        return links
            except httpx.RequestError:
                logger.warning("YouTube fallback scrape failed", exc_info=True)
                continue
        return links

    @staticmethod
    async def _fetch_videos_for_query_async(query, preferred_langs):
        videos = []

        for lang in preferred_langs:
            try:
                videos.extend(
                    await StudyContentService._fetch_videos_for_language_async(query, lang)
                )
            except httpx.RequestError:
                logger.warning("YouTube API request failed", exc_info=True)
            except httpx.HTTPStatusError:
                logger.warning("YouTube API returned non-2xx status", exc_info=True)
            except (KeyError, TypeError, ValueError):
                logger.warning("Unexpected YouTube API payload", exc_info=True)

        return videos
    @staticmethod
    async def _fetch_videos_for_language_async(query, lang):
        params = StudyContentService._build_youtube_params(query, lang)

        res = await safe_get_async(
            "https://www.googleapis.com/youtube/v3/search",
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS
        )

        expected_keywords = StudyContentService._extract_topic_keywords(query)
        return StudyContentService._extract_videos(res.json(), expected_keywords)
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
    def _extract_videos(data, expected_keywords=None):
        videos = []

        for item in data.get("items", []):
            try:
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                channel = item["snippet"]["channelTitle"]

                if StudyContentService.is_good_video(title, channel, expected_keywords):
                    videos.append(f"https://www.youtube.com/watch?v={video_id}")

            except (KeyError, TypeError):
                continue

        return videos
    @staticmethod
    def _extract_topic_keywords(text):
        words = re.findall(r"[a-z0-9]+", (text or "").lower())
        return [
            w for w in words
            if len(w) >= 4
            and w not in StudyContentService._STOPWORDS
            and w not in {"gate", "exam", "tutorial", "english", "hindi", "previous", "year", "questions", "solved", "practice", "full", "concepts", "mistakes", "tricks"}
        ]

    @staticmethod
    def _topic_relevance_score(title, expected_keywords):
        if not expected_keywords:
            return 1.0
        title_words = set(re.findall(r"[a-z0-9]+", (title or "").lower()))
        if not title_words:
            return 0.0
        matches = sum(1 for kw in set(expected_keywords) if kw in title_words)
        return matches / max(1, len(set(expected_keywords)))

    @staticmethod
    def is_good_video(title, channel_title="", expected_keywords=None):
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

        relevance_score = StudyContentService._topic_relevance_score(title, expected_keywords or [])
        if relevance_score < 0.34:
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
        return StudyContentService._generate_quick_content(topic)

    @staticmethod
    def _generate_quick_content(topic):
        topic_name = topic.name
        # Quick, synchronous best-effort fetch for first page load.
        queries = StudyContentService._default_queries(topic_name)[:2]
        videos = StudyContentService.fetch_youtube_videos(queries)
        description = StudyContentService._default_description(topic_name)
        if videos:
            StudyContentCache.objects.update_or_create(
                topic=topic,
                defaults={
                    "description": description,
                    "youtube_links": videos,
                },
            )
            return {
                "topic_id": topic.id,
                "topic_name": topic_name,
                "description": description,
                "youtube_links": videos,
            }
        return StudyContentService._build_pending_content(topic)

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
        links = videos or []

        StudyContentService._save_cache(topic, description, videos)

        return {
            "topic_id": topic.id,
            "topic_name": topic_name,
            "description": description,
            "youtube_links": links
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
