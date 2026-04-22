import os
import requests
from datetime import timedelta

from django.utils import timezone

from apps.analytics.models import StudyContentCache
from apps.roadmap.models import Topic
from groq import Groq


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
            return [
                f"{topic_name} GATE tutorial English",
                f"{topic_name} GATE exam problems English",
                f"{topic_name} GATE interview questions English"
            ]

        prompt = f"""
        Generate exactly only 3 high-quality YouTube search queries for GATE exam preparation on:
        {topic_name}

        Include (in order of priority):
        - GATE tutorial explanation (English)
        - GATE numerical problems solving
        - GATE previous year questions solutions

        Return only plain list (no numbering).
        Always add "GATE" and prefer "English" in queries for relevant results.
        """

        try:
            res = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            text = res.choices[0].message.content

            queries = [
                line.strip("- ").strip()
                for line in text.split("\n")
                if line.strip()
            ]

            return queries[:3]

        except Exception:
            return [
                f"{topic_name} tutorial",
                f"{topic_name} interview questions",
                f"{topic_name} problems"
            ]

    @staticmethod
    def generate_description(topic_name):
        client = StudyContentService.get_client()

        if not client:
            return f"{topic_name} is an important concept. Focus on understanding fundamentals and solving problems."

        prompt = f"""
        Explain {topic_name} in simple terms for students preparing for exams.
        Keep it short (5-6 lines).
        """

        try:
            res = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            return res.choices[0].message.content.strip()

        except Exception:
            return f"{topic_name} is an important concept. Focus on understanding fundamentals and solving problems."

    # ================= YOUTUBE FETCH =================
    @staticmethod
    def fetch_youtube_videos(queries):
        if not YOUTUBE_API_KEY:
            return []

        videos = []
        preferred_langs = ["English", "Telugu", "Hindi"]

        for query in queries:
            query_videos = StudyContentService._fetch_videos_for_query(query, preferred_langs)
            videos.extend(query_videos)
            if len(videos) >= 3:
                break

        return list(dict.fromkeys(videos))[:3]

    @staticmethod
    def _fetch_videos_for_query(query, preferred_langs):
        """Fetch videos for a single query across languages."""
        videos = []

        for lang in preferred_langs:
            search_query = "{} {}".format(query, lang)
            params = {
                "part": "snippet",
                "q": search_query,
                "key": YOUTUBE_API_KEY,
                "maxResults": 5,
                "type": "video",
                "videoDuration": "medium",
                "safeSearch": "strict"
            }

            try:
                res = requests.get(
                    "https://www.googleapis.com/youtube/v3/search",
                    params=params,
                    timeout=REQUEST_TIMEOUT_SECONDS
                )
                if res.status_code != 200:
                    continue

                for item in res.json().get("items", []):
                    video_id = item["id"]["videoId"]
                    title = item["snippet"]["title"]
                    channel_title = item["snippet"]["channelTitle"]

                    if StudyContentService.is_good_video(title, channel_title):
                        videos.append("https://www.youtube.com/watch?v={}".format(video_id))

            except Exception:
                continue

        return videos

    # ================= FILTER =================
    @staticmethod
    def is_good_video(title, channel_title=""):
        # Bad keywords to filter out
        bad_keywords = ["shorts", "trailer", "funny", "meme", "song", "lyrics", "comedy", "bollywood", "tollywood"]
        title_lower = title.lower()

        # Filter if contains bad keywords
        if any(word in title_lower for word in bad_keywords):
            return False

        # Filter out Tamil and other unwanted languages in title
        unwanted_langs = ["tamil", "தமிழ்", "malayalam", "മലയാളം", "kannada", "ಕನ್ನಡ", "bengali", "বাংলা", "punjabi", " Gujarati", "marathi"]
        if any(lang in title_lower for lang in unwanted_langs):
            return False

        # Filter if channel is regional language not wanted
        channel_lower = channel_title.lower()
        if any(lang in channel_lower for lang in unwanted_langs):
            return False

        return True

    # ================= MAIN =================
    @staticmethod
    def get_study_content(topic_name):
        if not topic_name:
            return None

        topic = Topic.objects.filter(name__iexact=str(topic_name).strip()).first()
        if not topic:
            return None

        # Check cache first
        cached = StudyContentService._get_cached_content(topic)
        if cached:
            return cached

        # Generate new content
        return StudyContentService._generate_and_cache(topic)

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
        """Generate and cache new study content."""
        topic_name = topic.name
        queries = StudyContentService.generate_queries(topic_name)
        videos = StudyContentService.fetch_youtube_videos(queries)
        description = StudyContentService.generate_description(topic_name)

        if videos:
            StudyContentCache.objects.update_or_create(
                topic=topic,
                defaults={
                    "description": description,
                    "youtube_links": videos
                }
            )

        return {
            "topic_id": topic.id,
            "topic_name": topic_name,
            "description": description,
            "youtube_links": videos
        }
