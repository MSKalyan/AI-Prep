import os
import requests
from datetime import timedelta

from django.utils import timezone

from apps.analytics.models import StudyContentCache
from apps.roadmap.models import Topic
from groq import Groq


YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


class StudyContentService:

    # ---------- GROQ CLIENT (SAFE) ----------
    @staticmethod
    def get_client():
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None
        return Groq(api_key=api_key)

    # ================= LLM: QUERY GENERATION =================
    @staticmethod
    def generate_queries(topic_name):
        client = StudyContentService.get_client()

        if not client:
            return [
                f"{topic_name} tutorial",
                f"{topic_name} interview questions",
                f"{topic_name} problems"
            ]

        prompt = f"""
        Generate exactly only 3 high-quality YouTube search queries for learning:
        {topic_name}

        Include:
        - beginner explanation
        - interview questions
        - problem solving

        Return only plain list (no numbering).
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

    # ================= LLM: DESCRIPTION =================
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
        videos = []

        if not YOUTUBE_API_KEY:
            return []

        for query in queries:
            url = "https://www.googleapis.com/youtube/v3/search"

            params = {
                "part": "snippet",
                "q": query,
                "key": YOUTUBE_API_KEY,
                "maxResults": 3,
                "type": "video",
                "videoDuration": "medium",
                "safeSearch": "strict"
            }

            try:
                res = requests.get(url, params=params)
                data = res.json()

                for item in data.get("items", []):
                    video_id = item["id"]["videoId"]
                    title = item["snippet"]["title"]

                    if StudyContentService.is_good_video(title):
                        videos.append(
                            f"https://www.youtube.com/watch?v={video_id}"
                        )

            except Exception:
                continue

        return list(dict.fromkeys(videos))[:3]

    # ================= FILTER =================
    @staticmethod
    def is_good_video(title):
        bad_keywords = ["shorts", "trailer", "funny", "meme"]
        return not any(word in title.lower() for word in bad_keywords)

    # ================= MAIN =================
    @staticmethod
    def get_study_content(topic_name):
        try:
            topic = Topic.objects.filter(name__iexact=topic_name).first()
        except Topic.DoesNotExist:
            return None

        cached = StudyContentCache.objects.filter(topic=topic).first()

        if (
            cached
            and cached.youtube_links
            and (timezone.now() - cached.created_at) < timedelta(days=7)
        ):
            return {
                "topic_id": topic.id,
                "topic_name": topic.name,
                "description": cached.description,
                "youtube_links": cached.youtube_links
            }

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