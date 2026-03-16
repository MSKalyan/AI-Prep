import re


def parse_syllabus(text):

    syllabus = []

    sections = re.split(r"Section\s+\d+\s*:\s*", text)

    for section in sections[1:]:

        lines = [l.strip() for l in section.split("\n") if l.strip()]

        if not lines:
            continue

        subject = lines[0]

        topics = []

        for line in lines[1:]:

            # Case 1: Topic with subtopics
            if ":" in line:

                topic, rest = line.split(":", 1)

                topic = topic.strip()

                subtopics = [
                    s.strip().rstrip(".")
                    for s in re.split(r"[;,\.]", rest)
                    if s.strip()
                ]

                topics.append({
                    "topic": topic,
                    "subtopics": subtopics
                })

            # Case 2: Multiple topics in one line
            else:

                split_topics = [
                    t.strip().rstrip(".")
                    for t in re.split(r"[.,]", line)
                    if t.strip()
                ]

                for t in split_topics:
                    topics.append({
                        "topic": t,
                        "subtopics": []
                    })

        syllabus.append({
            "subject": subject,
            "topics": topics
        })

    return syllabus