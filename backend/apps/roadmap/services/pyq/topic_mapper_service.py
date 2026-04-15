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

        scores = defaultdict(int)

        # keyword matching
        for keyword, subject_name in TopicMapperService.MAP.items():
            if keyword in text:
                scores[subject_name] += len(keyword)

        # topic name matching - more specific
        topic_map = TopicMapperService.load_topics_for_exam(exam)

        topic_scores = {}
        for normalized_topic, topic_obj in topic_map.items():
            if normalized_topic in text:
                # Score by topic name length (longer = more specific)
                topic_scores[topic_obj.id] = len(normalized_topic)

        if topic_scores:
            # Return the most specific topic match
            best_topic_id = max(topic_scores, key=topic_scores.get)
            best_topic = Topic.objects.get(id=best_topic_id)
            return best_topic

        if not scores:
            return None

        best_topic_name = max(scores, key=scores.get)

        # Try to find the topic with this name
        matching_topic = Topic.objects.filter(
            name=best_topic_name, subject__exam=exam
        ).first()

        if matching_topic:
            return matching_topic

        # Try partial match
        matching_topic = Topic.objects.filter(
            subject__exam=exam, name__icontains=best_topic_name.split()[0]
        ).first()

        if matching_topic:
            return matching_topic

        topic = Topic.objects.filter(
            subject__exam=exam, subject__name="Engineering Mathematics"
        ).first()

        return topic
