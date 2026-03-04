def build_roadmap_explanation_prompt(topic: str, subject: str, week: int, phase: str):

    return f"""
You are an AI tutor helping students prepare for exams.

You will receive a roadmap topic. Your job is to provide a short explanation of the topic.

STRICT RULES:
1. Do NOT modify the topic name.
2. Do NOT change week numbers.
3. Do NOT change roadmap structure.
4. Do NOT add extra commentary.
5. Keep explanation concise and educational.
6. Maximum 3 sentences.

Roadmap Topic Information:

Topic: {topic}
Subject: {subject}
Week: {week}
Phase: {phase}

Return ONLY valid JSON in the following format:

{{
  "topic": "{topic}",
  "explanation": "clear and short explanation of the topic"
}}
"""