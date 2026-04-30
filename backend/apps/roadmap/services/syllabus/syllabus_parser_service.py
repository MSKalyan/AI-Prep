import re


def parse_syllabus(text):
    syllabus = []
    sections = re.split(r"Section\s+\d+\s*:\s*", text)
    for section in sections[1:]:
        lines = _extract_non_empty_lines(section)
        if not lines:
            continue
        subject = lines[0]
        topics = _parse_lines_to_topics(lines[1:])
        syllabus.append({"subject": subject, "topics": topics})
    return syllabus


def _extract_non_empty_lines(section):
    return [line.strip() for line in section.split("\n") if line.strip()]


def _parse_lines_to_topics(lines):
    topics = []
    for line in lines:
        if ":" in line:
            topics.append(_parse_topic_with_subtopics(line))
            continue
        topics.extend(_parse_inline_topics(line))
    return topics


def _parse_topic_with_subtopics(line):
    topic, rest = line.split(":", 1)
    subtopics = [s.strip().rstrip(".") for s in re.split(r"[;,\.]", rest) if s.strip()]
    return {"topic": topic.strip(), "subtopics": subtopics}


def _parse_inline_topics(line):
    split_topics = [t.strip().rstrip(".") for t in re.split(r"[.,]", line) if t.strip()]
    return [{"topic": topic, "subtopics": []} for topic in split_topics]
