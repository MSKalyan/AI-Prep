class TopicMapperService:

    MAP = {

        # Computer Organization
        "hazard": "Computer Organization & Architecture",
        "pipeline": "Computer Organization & Architecture",
        "floating point": "Computer Organization & Architecture",
        "addressing": "Computer Organization & Architecture",
        "cache": "Computer Organization & Architecture",

        # Operating Systems
        "deadlock": "Operating Systems",
        "banker": "Operating Systems",
        "process": "Operating Systems",
        "scheduling": "Operating Systems",

        # Algorithms
        "graph": "Algorithms",
        "shortest path": "Algorithms",
        "dynamic programming": "Algorithms",

        # Databases
        "sql": "Databases",
        "normalization": "Databases",

        # Networks
        "tcp": "Computer Networks",
        "routing": "Computer Networks",
        "arp": "Computer Networks",

        # Mathematics
        "expectation": "Engineering Mathematics",
        "eigen": "Engineering Mathematics",
        "probability": "Engineering Mathematics",
        "combinatorics": "Engineering Mathematics",
    }

    @staticmethod
    def map_topic(tag):

        tag = tag.lower()

        for key, topic in TopicMapperService.MAP.items():

            if key in tag:
                return topic

        return None