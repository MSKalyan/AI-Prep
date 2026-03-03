from django.core.management.base import BaseCommand
from apps.roadmap.models import Exam, Topic


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        exam, _ = Exam.objects.get_or_create(
            name="GATE CSE"
        )

        syllabus = {
            "Engineering Mathematics": [
                "Linear Algebra",
                "Calculus",
                "Probability & Statistics"
            ],
            "Programming & Data Structures": [
                "Arrays",
                "Linked Lists",
                "Stacks & Queues",
                "Trees",
                "Graphs"
            ],
            "Algorithms": [
                "Sorting",
                "Searching",
                "Dynamic Programming",
                "Greedy Algorithms"
            ],
            "Operating Systems": [
                "Processes",
                "Scheduling",
                "Memory Management",
                "Deadlocks"
            ],
            "Databases": [
                "ER Model",
                "SQL",
                "Normalization",
                "Transactions"
            ],
            "Computer Networks": [
                "OSI Model",
                "TCP/IP",
                "Routing",
                "Congestion Control"
            ],
            "Computer Organization & Architecture": [
                "Pipelining",
                "Memory Hierarchy",
                "Instruction Set"
            ],
            "Theory of Computation": [
                "Regular Languages",
                "Context Free Grammars",
                "Turing Machines"
            ],
            "Compiler Design": [
                "Lexical Analysis",
                "Parsing",
                "Code Generation"
            ],
            "Digital Logic": [
                "Boolean Algebra",
                "Combinational Circuits",
                "Sequential Circuits"
            ]
        }

        order_counter = 0

        for subject, subtopics in syllabus.items():

            parent_topic, _ = Topic.objects.get_or_create(
                exam=exam,
                name=subject,
                parent=None,
                order=order_counter,
                is_core=True
            )

            order_counter += 1

            for sub_index, sub in enumerate(subtopics):

                Topic.objects.get_or_create(
                    exam=exam,
                    name=sub,
                    parent=parent_topic,
                    order=sub_index,
                    is_core=True
                )

        self.stdout.write(self.style.SUCCESS("GATE CSE syllabus seeded successfully"))