import re
from collections import defaultdict

from apps.roadmap.models import Topic


class TopicMapperService:

    # keyword → SUBJECT name (must match DB exactly)
    MAP = {

        # Engineering Mathematics
        "probability": "Engineering Mathematics",
        "statistics": "Engineering Mathematics",
        "expectation": "Engineering Mathematics",
        "combinatorics": "Engineering Mathematics",
        "linear algebra": "Engineering Mathematics",
        "eigen": "Engineering Mathematics",
        "calculus": "Engineering Mathematics",
        "set theory": "Engineering Mathematics",
        "logic": "Engineering Mathematics",
        "numerical": "Engineering Mathematics",

        # Programming and Data Structures
        "data structure": "Programming and Data Structures",
        "linked list": "Programming and Data Structures",
        "stack": "Programming and Data Structures",
        "queue": "Programming and Data Structures",
        "tree": "Programming and Data Structures",
        "heap": "Programming and Data Structures",
        "array": "Programming and Data Structures",
        "pointer": "Programming and Data Structures",
        "recursion": "Programming and Data Structures",

        # Algorithms
        "graph": "Algorithms",
        "shortest path": "Algorithms",
        "dynamic programming": "Algorithms",
        "sorting": "Algorithms",
        "search": "Algorithms",
        "greedy": "Algorithms",
        "complexity": "Algorithms",

        # Operating System
        "process": "Operating System",
        "thread": "Operating System",
        "deadlock": "Operating System",
        "banker": "Operating System",
        "scheduling": "Operating System",
        "memory management": "Operating System",
        "virtual memory": "Operating System",
        "file system": "Operating System",
        "paging": "Operating System",

        # Computer Organization and Architecture
        "pipeline": "Computer Organization and Architecture",
        "pipelining": "Computer Organization and Architecture",
        "hazard": "Computer Organization and Architecture",
        "cache": "Computer Organization and Architecture",
        "instruction": "Computer Organization and Architecture",
        "floating point": "Computer Organization and Architecture",
        "microprogramming": "Computer Organization and Architecture",
        "alu": "Computer Organization and Architecture",
        "memory hierarchy": "Computer Organization and Architecture",

        # Computer Networks
        "tcp": "Computer Networks",
        "udp": "Computer Networks",
        "routing": "Computer Networks",
        "arp": "Computer Networks",
        "dhcp": "Computer Networks",
        "icmp": "Computer Networks",
        "ethernet": "Computer Networks",
        "network": "Computer Networks",

        # Databases
        "sql": "Databases",
        "normalization": "Databases",
        "er model": "Databases",
        "transaction": "Databases",
        "relational": "Databases",
        "database": "Databases",

        # Theory of Computation
        "regular language": "Theory of Computation",
        "finite automata": "Theory of Computation",
        "turing": "Theory of Computation",
        "grammar": "Theory of Computation",
        "pumping lemma": "Theory of Computation",
        "automata": "Theory of Computation",

        # Compiler Design
        "compiler": "Compiler Design",
        "lexical": "Compiler Design",
        "parsing": "Compiler Design",
        "code generation": "Compiler Design",
        "syntax": "Compiler Design",

        # Digital Logic
        "boolean": "Digital Logic",
        "combinational": "Digital Logic",
        "sequential": "Digital Logic",
        "logic gate": "Digital Logic",
        "flip flop": "Digital Logic",
    }

    topic_cache = {}

    @staticmethod
    def normalize(text):

        if not text:
            return ""

        text = text.lower()
        text = text.replace("-", " ")
        text = text.replace("_", " ")
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def load_topics_for_exam(exam):

        if exam.id in TopicMapperService.topic_cache:
            return TopicMapperService.topic_cache[exam.id]

        topics = Topic.objects.filter(subject__exam=exam)

        topic_map = {}

        for topic in topics:
            topic_map[TopicMapperService.normalize(topic.name)] = topic

        TopicMapperService.topic_cache[exam.id] = topic_map

        return topic_map

    @staticmethod
    def map_topic(question_text, exam=None):

        if not question_text or exam is None:
            return None

        text = TopicMapperService.normalize(question_text)

        scores = defaultdict(int)

        # keyword matching
        for keyword, subject_name in TopicMapperService.MAP.items():

            if keyword in text:
                scores[subject_name] += len(keyword)

        # topic name matching
        topic_map = TopicMapperService.load_topics_for_exam(exam)

        for normalized_topic, topic_obj in topic_map.items():

            if normalized_topic in text:
                scores[topic_obj.subject.name] += 3

        if not scores:
            return None

        best_subject = max(scores, key=scores.get)

        # return a topic from that subject (first topic)
        topic = Topic.objects.filter(
            subject__name=best_subject,
            subject__exam=exam
        ).first()

        return topic