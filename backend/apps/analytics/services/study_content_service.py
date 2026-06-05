import os
import logging
import re
import requests
from datetime import timedelta

from django.utils import timezone
from django.conf import settings

from apps.analytics.models import StudyContentCache
from apps.roadmap.models import Topic
from groq import Groq
from apps.utils.retry_utils import safe_get, safe_llm_call

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
            f"{base} GATE CS tutorial concepts explained",
            f"{base} exam preparation lecture",
            f"{base} problem solving tricks"
        ]

    @staticmethod
    def _call_llm_for_queries(client, topic_name):
        prompt = f"""
Generate exactly 3 specific YouTube search queries for learning {topic_name} for GATE exams.
Each query should focus on understanding concepts, not just exam tips.

Return only 3 lines with the queries, no numbering.
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
        if not YOUTUBE_API_KEY:
            return StudyContentService._scrape_youtube_video_links(queries)
        
        videos = []
        preferred_langs = ["English", "Hindi"]
        for query in queries:
            query_videos = StudyContentService._fetch_videos_for_query(query, preferred_langs)
            videos.extend(query_videos)
            if len(videos) >= 3:
                break
        
        deduped = list(dict.fromkeys(videos))[:3]
        if deduped:
            return deduped
        return StudyContentService._scrape_youtube_video_links(queries)

    @staticmethod
    def _scrape_youtube_video_links(queries):
        seen_ids = set()
        links = []
        for query in queries:
            try:
                search_url = "https://www.youtube.com/results"
                res = safe_get(
                    search_url,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    params={"search_query": query},
                )
                video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", res.text or "")
                unique_ids = list(dict.fromkeys(video_ids))[:5]
                for video_id in unique_ids:
                    if video_id not in seen_ids:
                        seen_ids.add(video_id)
                        links.append({
                            "title": f"Video {video_id}",
                            "video_id": video_id,
                            "thumbnail": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                        })
                    if len(links) >= 3:
                        return links
            except Exception as e:
                logger.warning(f"YouTube fallback scrape failed: {e}")
                continue
        return links

    @staticmethod
    def _fetch_videos_for_query(query, preferred_langs):
        videos = []
        for lang in preferred_langs:
            try:
                videos.extend(
                    StudyContentService._fetch_videos_for_language(query, lang)
                )
            except Exception as e:
                logger.warning(f"YouTube API request failed: {e}")
        return videos

    @staticmethod
    def _fetch_videos_for_language(query, lang):
        params = StudyContentService._build_youtube_params(query, lang)
        res = safe_get(
            "https://www.googleapis.com/youtube/v3/search",
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        expected_keywords = StudyContentService._extract_topic_keywords(query)
        return StudyContentService._extract_videos(res.json(), expected_keywords)

    @staticmethod
    def _build_youtube_params(query, lang):
        enhanced_query = f"{query} tutorial concept explained lecture"
        return {
            "part": "snippet",
            "q": enhanced_query,
            "type": "video",
            "maxResults": 10,
            "key": YOUTUBE_API_KEY,
            "relevanceLanguage": lang
        }

    @staticmethod
    def _extract_topic_keywords(query):
        return {
            w for w in re.findall(r"\w+", query.lower())
            if w not in StudyContentService._STOPWORDS and len(w) > 2
        }

    @staticmethod
    def _extract_videos(response_data, expected_keywords):
        videos = []
        try:
            for item in response_data.get("items", []):
                title = item.get("snippet", {}).get("title", "").lower()
                if any(k in title for k in expected_keywords):
                    videos.append({
                        "title": item["snippet"]["title"],
                        "video_id": item["id"]["videoId"],
                        "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"]
                    })
        except (KeyError, TypeError, ValueError):
            logger.warning("Unexpected YouTube API payload", exc_info=True)
        return videos

    @staticmethod
    def get_study_content(topic_name):
        try:
            from apps.roadmap.models import Topic
            topic_obj = Topic.objects.filter(name__iexact=topic_name).first()
            
            if topic_obj:
                cached = StudyContentCache.objects.filter(topic=topic_obj).first()
                if cached and (timezone.now() - cached.created_at).days < 7:
                    return StudyContentService._parse_cached_content(cached)

            queries = StudyContentService.generate_queries(topic_name)
            youtube_links = StudyContentService.fetch_youtube_videos(queries)
            description = StudyContentService.generate_description(topic_name)

            content = {
                "topic": topic_name,
                "description": description,
                "youtube_videos": youtube_links[:3],
                "queries_used": queries,
                "generated_at": timezone.now().isoformat()
            }

            if topic_obj:
                StudyContentService._cache_content(topic_obj, content)
            return content

        except Exception as e:
            logger.error(f"get_study_content failed: {e}", exc_info=True)
            return StudyContentService._get_fallback_content(topic_name)

    @staticmethod
    def _parse_cached_content(cached):
        return {
            "topic": cached.topic.name,
            "description": cached.description,
            "youtube_videos": cached.youtube_links[:3] if cached.youtube_links else [],
            "generated_at": cached.created_at.isoformat()
        }

    @staticmethod
    def _cache_content(topic_obj, content):
        StudyContentCache.objects.update_or_create(
            topic=topic_obj,
            defaults={
                "description": content["description"],
                "youtube_links": content["youtube_videos"],
            }
        )

    @staticmethod
    def _get_fallback_content(topic_name):
        return {
            "topic": topic_name,
            "description": f"{topic_name} is an important concept.",
            "youtube_videos": [],
            "queries_used": [],
            "generated_at": timezone.now().isoformat()
        }

    @staticmethod
    def _generate_quick_content(topic):
        queries = StudyContentService._get_quick_queries(topic)
        videos = StudyContentService.fetch_youtube_videos(queries) if queries else []
        return {
            "topic": topic,
            "description": f"{topic} - important for GATE exam",
            "youtube_videos": videos,
        }

    @staticmethod
    def _get_quick_queries(topic):
        return [f"{topic} GATE tutorial", f"{topic} GATE PYQs"]