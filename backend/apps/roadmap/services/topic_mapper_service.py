import re


class TopicMapperService:

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
        "mathematical logic": "Engineering Mathematics",
        "numerical methods": "Engineering Mathematics",

        # Programming & Data Structures
        "data structure": "Programming & Data Structures",
        "linked list": "Programming & Data Structures",
        "stack": "Programming & Data Structures",
        "queue": "Programming & Data Structures",
        "tree": "Programming & Data Structures",
        "heap": "Programming & Data Structures",
        "array": "Programming & Data Structures",
        "programming": "Programming & Data Structures",

        # Algorithms
        "graph": "Algorithms",
        "shortest path": "Algorithms",
        "dynamic programming": "Algorithms",
        "sorting": "Algorithms",
        "search": "Algorithms",
        "greedy": "Algorithms",
        "algorithm": "Algorithms",

        # Operating Systems
        "process": "Operating Systems",
        "thread": "Operating Systems",
        "deadlock": "Operating Systems",
        "banker": "Operating Systems",
        "scheduling": "Operating Systems",
        "memory management": "Operating Systems",
        "virtual memory": "Operating Systems",
        "file system": "Operating Systems",
        "operating system": "Operating Systems",

        # Computer Organization & Architecture
        "pipeline": "Computer Organization & Architecture",
        "hazard": "Computer Organization & Architecture",
        "cache": "Computer Organization & Architecture",
        "addressing": "Computer Organization & Architecture",
        "floating point": "Computer Organization & Architecture",
        "instruction": "Computer Organization & Architecture",
        "alu": "Computer Organization & Architecture",
        "coa": "Computer Organization & Architecture",

        # Computer Networks
        "tcp": "Computer Networks",
        "udp": "Computer Networks",
        "routing": "Computer Networks",
        "arp": "Computer Networks",
        "dhcp": "Computer Networks",
        "icmp": "Computer Networks",
        "ip": "Computer Networks",
        "ethernet": "Computer Networks",
        "network": "Computer Networks",
        "web technologies": "Computer Networks",

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
        "digital logic": "Digital Logic",

        # General Aptitude
        "verbal aptitude": "General Aptitude",
        "analytical aptitude": "General Aptitude",
        "quantitative aptitude": "General Aptitude",
        "spatial aptitude": "General Aptitude",
        "logical reasoning": "General Aptitude",
        "general aptitude": "General Aptitude",
    }

    @staticmethod
    def normalize(tag):
        tag = tag.lower()
        tag = tag.replace("-", " ")
        tag = tag.replace("_", " ")
        tag = re.sub(r"\s+", " ", tag)
        return tag.strip()

    @staticmethod
    def map_topic(candidates):

        if not candidates:
            return None

        for tag in candidates:

            tag = TopicMapperService.normalize(tag)

            for key, topic in TopicMapperService.MAP.items():

                if key in tag:
                    return topic

        return None