import re
from collections import defaultdict

from apps.roadmap.models import Topic


class TopicMapperService:
    # Constants to avoid duplicate string literals
    PROB_STATS = "Probability and Statistics"
    DISCRETE_MATH = "Discrete Mathematics"
    ENG_MATH = "Engineering Mathematics"
    CALCULUS = "Calculus"
    PROG_DS = "Programming and Data Structures"
    OS = "Operating System"
    MEM_MGMT = "Memory management and virtual memory"
    COA = "Computer Organization and Architecture"
    CN = "Computer Networks"
    DB = "Databases"
    REG_AUTOMATA = "Regular expressions and finite automata"
    INTER_CODE = "Intermediate code"
    COMB_SEQ = "Combinational and sequential circuits"
    LATTICES = "lattices. Monoids, Groups. Graphs"
    INST_PIPE = "Instruction pipelining"
    APP_PROTO = "Application layer protocols"
    CIDR = "CIDR notation"
    ER_MODEL = "ER‐model. Relational model"
    PUMP_LEMMA = "pumping lemma"

    # keyword → SUBJECT name (must match DB exactly)
    MAP = {
        # Engineering Mathematics
        "probability": PROB_STATS,
        "statistics": PROB_STATS,
        "expectation": PROB_STATS,
        "random": PROB_STATS,
        "bayes": PROB_STATS,
        "combinatorics": DISCRETE_MATH,
        "permutation": DISCRETE_MATH,
        "combination": DISCRETE_MATH,
        "graphs": LATTICES,
        "graph theory": LATTICES,
        "vertex": LATTICES,
        "edge": LATTICES,
        "linear algebra": ENG_MATH,
        "eigen": ENG_MATH,
        "matrix": ENG_MATH,
        "determinant": ENG_MATH,
        "calculus": CALCULUS,
        "derivative": CALCULUS,
        "integral": CALCULUS,
        "set theory": DISCRETE_MATH,
        "logic gates": DISCRETE_MATH,
        "proposition": DISCRETE_MATH,
        "boolean algebra": DISCRETE_MATH,
        "numerical methods": ENG_MATH,
        # Programming and Data Structures
        "data structure": PROG_DS,
        "linked list": PROG_DS,
        "stack": "stacks",
        "queue": "queues",
        "tree": PROG_DS,
        "heap": PROG_DS,
        "array": "Arrays",
        "pointer": PROG_DS,
        "recursion": "Recursion",
        # Algorithms
        "algorithm": "Algorithms",
        "graph": "graphs",
        "shortest path": "Algorithms",
        "dynamic programming": "Algorithms",
        "sorting": "Algorithms",
        "search": "Searching",
        "greedy": "Algorithms",
        "complexity": "Algorithms",
        "time complexity": "Algorithms",
        "space complexity": "Algorithms",
        # Operating System
        "process": "processes",
        "thread": "threads",
        "deadlock": OS,
        "banker": OS,
        "scheduling": OS,
        "memory management": MEM_MGMT,
        "virtual memory": MEM_MGMT,
        "file system": "File organization",
        "paging": MEM_MGMT,
        "system call": "System calls",
        # Computer Organization and Architecture
        "pipeline": INST_PIPE,
        "pipelining": INST_PIPE,
        "hazard": INST_PIPE,
        "cache": COA,
        "instruction": "Machine instructions and addressing modes",
        "floating point": COA,
        "microprogramming": COA,
        "alu": "data‐path and control unit",
        "memory hierarchy": COA,
        # Computer Networks
        "tcp": APP_PROTO,
        "udp": APP_PROTO,
        "routing": "Routing protocols",
        "arp": "Basics of IP support protocols (ARP",
        "dhcp": "DHCP",
        "icmp": APP_PROTO,
        "ethernet": CN,
        "network": CN,
        "ip address": CIDR,
        "subnet": CIDR,
        "cidr": CIDR,
        # Databases
        "sql": DB,
        "normalization": DB,
        "er model": ER_MODEL,
        "relational": ER_MODEL,
        "database": DB,
        "transaction": DB,
        # Theory of Computation
        "regular language": REG_AUTOMATA,
        "finite automata": REG_AUTOMATA,
        "turing": "Turing machines and undecidability",
        "grammar": PUMP_LEMMA,
        "pumping lemma": PUMP_LEMMA,
        "automata": REG_AUTOMATA,
        # Compiler Design
        "compiler": INTER_CODE,
        "lexical": INTER_CODE,
        "parsing": INTER_CODE,
        "code generation": INTER_CODE,
        "syntax": INTER_CODE,
        "runtime": "Runtime environments",
        # Digital Logic
        "boolean": "Digital Logic",
        "combinational": COMB_SEQ,
        "sequential": COMB_SEQ,
        "logic gate": "Digital Logic",
        "flip flop": COMB_SEQ,
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
        topic_map = TopicMapperService.load_topics_for_exam(exam)
        topic_scores = TopicMapperService._build_topic_scores(text, topic_map)
        if topic_scores:
            return TopicMapperService._get_best_topic_from_scores(topic_scores)

        scores = TopicMapperService._build_keyword_scores(text)
        if not scores:
            return None

        best_topic_name = max(scores, key=scores.get)
        matching_topic = TopicMapperService._find_topic_by_name(exam, best_topic_name)
        if matching_topic:
            return matching_topic

        return TopicMapperService._get_engineering_math_fallback(exam)

    @staticmethod
    def _build_keyword_scores(text):
        scores = defaultdict(int)
        for keyword, subject_name in TopicMapperService.MAP.items():
            if keyword in text:
                scores[subject_name] += len(keyword)
        return scores

    @staticmethod
    def _build_topic_scores(text, topic_map):
        topic_scores = {}
        for normalized_topic, topic_obj in topic_map.items():
            if normalized_topic in text:
                topic_scores[topic_obj.id] = len(normalized_topic)
        return topic_scores

    @staticmethod
    def _get_best_topic_from_scores(topic_scores):
        best_topic_id = max(topic_scores, key=topic_scores.get)
        return Topic.objects.get(id=best_topic_id)

    @staticmethod
    def _find_topic_by_name(exam, best_topic_name):
        matching_topic = Topic.objects.filter(name=best_topic_name, subject__exam=exam).first()
        if matching_topic:
            return matching_topic
        matching_topic = Topic.objects.filter(
            subject__exam=exam, name__icontains=best_topic_name.split()[0]
        ).first()
        return matching_topic

    @staticmethod
    def _get_engineering_math_fallback(exam):
        return Topic.objects.filter(
            subject__exam=exam, subject__name="Engineering Mathematics"
        ).first()
