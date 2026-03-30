import os
from apps.analytics.models import StudyContentCache
from datetime import timedelta
from django.utils import timezone

from apps.roadmap.models import Topic
from groq import Groq
import requests
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
class StudyContentService:

  


    # ================= LLM: QUERY GENERATION =================
    @staticmethod
    def generate_queries(topic_name):
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
            # fallback (IMPORTANT)
            return [
                f"{topic_name} tutorial",
                f"{topic_name} interview questions",
                f"{topic_name} problems"
            ]

    # ================= LLM: DESCRIPTION =================
    @staticmethod
    def generate_description(topic_name):
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

        for query in queries:
            url = "https://www.googleapis.com/youtube/v3/search"

            params = {
                "part": "snippet",
                "q": query,
                "key": YOUTUBE_API_KEY,
                "maxResults": 3,
                "type": "video",
                "videoDuration": "medium",   # avoid shorts
                "safeSearch": "strict"
            }

            try:
                res = requests.get(url, params=params)
                data = res.json()
                print(data)
                for item in data.get("items", []):
                    video_id = item["id"]["videoId"]
                    title = item["snippet"]["title"]

                    # filter low-quality videos
                    if StudyContentService.is_good_video(title):
                        videos.append(
                            f"https://www.youtube.com/watch?v={video_id}"
                        )

            except Exception:
                continue

        # remove duplicates + limit
        return list(dict.fromkeys(videos))[:3]

    # ================= FILTER =================
    @staticmethod
    def is_good_video(title):
        bad_keywords = ["shorts", "trailer", "funny", "meme"]

        title = title.lower()

        return not any(word in title for word in bad_keywords)

    @staticmethod
    def get_study_content(topic_id):
        try:
            topic = Topic.objects.get(id=topic_id)
        except Topic.DoesNotExist:
            return None

        # ✅ STEP 1 — Check cache
        cached = StudyContentCache.objects.filter(topic=topic).first()

        if (
            cached
            and cached.youtube_links   # 🔥 ensure not empty
            and (timezone.now() - cached.created_at) < timedelta(days=7)
        ):
            return {
                "topic_id": topic.id,
                "topic_name": topic.name,
                "description": cached.description,
                "youtube_links": cached.youtube_links
            }

        # ✅ STEP 2 — Generate (only once)
        topic_name = topic.name

        queries = StudyContentService.generate_queries(topic_name)
        videos = StudyContentService.fetch_youtube_videos(queries)
        description = StudyContentService.generate_description(topic_name)

        # ✅ STEP 3 — Save cache
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
    
   