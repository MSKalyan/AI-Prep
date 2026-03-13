import re


def clean_lines(text):

    lines = text.split("\n")

    cleaned = []
    buffer = ""

    for line in lines:

        line = line.strip()

        if not line:
            continue

        if buffer and not buffer.endswith(":") and not line.startswith("Section"):
            buffer += " " + line
        else:
            if buffer:
                cleaned.append(buffer)
            buffer = line

    if buffer:
        cleaned.append(buffer)

    return cleaned


def parse_syllabus(text):

    lines = clean_lines(text)

    syllabus = {}
    current_subject = None

    for line in lines:

        # Detect subject sections
        section_match = re.match(r"Section\s+\d+\s*:\s*(.+)", line)

        if section_match:

            subject_name = section_match.group(1).strip()

            subject_name = subject_name.replace("Core Topics", "")
            subject_name = subject_name.replace("Special Topics", "")

            subject_name = subject_name.strip()

            # ignore corrupted lines
            if ":" in subject_name or len(subject_name) > 80:
                continue

            current_subject = subject_name

            syllabus[current_subject] = {}

            continue

        if current_subject is None:
            continue

        # Detect multiple topics inside the same line
        topic_matches = re.findall(r"([A-Za-z\s\(\)]+?):", line)

        if topic_matches:

            parts = re.split(r"([A-Za-z\s\(\)]+?:)", line)

            for i in range(1, len(parts), 2):

                topic = parts[i].replace(":", "").strip()

                if i + 1 < len(parts):
                    subtopics_raw = parts[i + 1]

                    subtopics = [
                        s.strip().rstrip(".")
                        for s in re.split(r"[;,]", subtopics_raw)
                        if s.strip()
                    ]

                    syllabus[current_subject][topic] = subtopics

    return syllabus