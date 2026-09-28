from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from learning.models import Answer, AttendanceSession, DemoConfig, Homework, Lesson, Question, Student, Submission


LESSONS = [
    {
        "key": "linear",
        "title": "Linear equations: see the structure",
        "subject": "math",
        "topic": "Algebra · Linear equations",
        "duration_minutes": 6,
        "summary": "Turn word problems into equations, isolate the variable, and check the result efficiently.",
        "material": "Name the unknown first. Translate one relationship at a time, then simplify both sides before isolating the variable. On the digital SAT, a quick substitution check often catches sign errors faster than reworking the algebra.",
        "progress_percent": 68,
        "is_today": True,
        "sort_order": 1,
        "homework_title": "Linear equations checkpoint",
        "homework_description": "Apply today’s equation-building strategy in four focused questions.",
        "deadline_days": 2,
        "questions": [
            ("A gym charges a $24 joining fee plus $18 per month. If Maya paid $132, how many months did she pay for?", "5", "6", "7", "8", "B", "Write 24 + 18m = 132. Then 18m = 108, so m = 6."),
            ("For 3(x − 4) = 2x + 7, what is the value of x?", "11", "15", "19", "23", "C", "Expand to 3x − 12 = 2x + 7, then subtract 2x and add 12 to get x = 19."),
            ("A line passes through (2, 7) and (6, 19). What is its slope?", "2", "3", "4", "6", "B", "Slope is the change in y divided by the change in x: (19 − 7)/(6 − 2) = 12/4 = 3."),
            ("If 5y + 8 = 3y + 26, what is y?", "7", "8", "9", "17", "C", "Subtract 3y and 8 from both sides: 2y = 18, so y = 9."),
        ],
    },
    {
        "key": "transitions",
        "title": "Transitions that reveal logic",
        "subject": "rw",
        "topic": "Expression of Ideas · Transitions",
        "duration_minutes": 7,
        "summary": "Choose transitions by naming the logical relationship before looking at the options.",
        "material": "Read the sentences without the blank and describe their relationship in plain language: contrast, cause, example, continuation, or conclusion. Only then choose the transition that expresses that relationship with the correct punctuation.",
        "progress_percent": 42,
        "is_today": False,
        "sort_order": 2,
        "homework_title": "Transition logic practice",
        "homework_description": "Identify the relationship between ideas before choosing the connector.",
        "deadline_days": 4,
        "questions": [
            ("The trail looked short on the map. ___, its steep switchbacks made the hike demanding.", "Similarly", "However", "For example", "Therefore", "B", "The second sentence contrasts with the expectation created by the first, so ‘However’ fits."),
            ("The archive digitized its rare maps. ___, researchers worldwide can now study them.", "As a result", "Nevertheless", "Meanwhile", "In contrast", "A", "Worldwide access is a result of digitization."),
            ("Many desert plants store water in thick stems. ___, the saguaro expands after rainfall.", "Instead", "For instance", "Otherwise", "Likewise", "B", "The saguaro is a specific example of the general statement."),
            ("The first trial produced inconsistent readings. ___, the team recalibrated the sensor before continuing.", "In addition", "Previously", "Consequently", "For comparison", "C", "Recalibration is a consequence of the inconsistent readings."),
        ],
    },
    {
        "key": "ratios",
        "title": "Ratios, rates, and proportional reasoning",
        "subject": "math",
        "topic": "Problem-Solving and Data Analysis",
        "duration_minutes": 8,
        "summary": "Use units to organize multistep rate and proportion questions.",
        "material": "Write units beside every quantity. Set up equivalent ratios in the same order, then estimate before calculating so an inverted ratio is easy to spot.",
        "progress_percent": 100,
        "is_today": False,
        "sort_order": 3,
        "homework_title": "Rates and ratios review",
        "homework_description": "A short review of unit rates and equivalent ratios.",
        "deadline_days": -3,
        "questions": [
            ("A car travels 156 miles on 6 gallons. What is the unit rate?", "24 mpg", "25 mpg", "26 mpg", "28 mpg", "C", "Divide 156 miles by 6 gallons to get 26 miles per gallon."),
            ("The ratio of red to blue tiles is 3:5. If there are 30 blue tiles, how many are red?", "15", "18", "20", "25", "B", "The scale factor is 30 ÷ 5 = 6, so there are 3 × 6 = 18 red tiles."),
            ("Four notebooks cost $11. At the same rate, what do 10 notebooks cost?", "$22.00", "$25.50", "$27.50", "$30.00", "C", "Each notebook costs $2.75, and 10 cost $27.50."),
            ("A recipe uses 2.5 cups of flour for 20 cookies. How many cups are needed for 32 cookies?", "3", "3.5", "4", "4.5", "C", "Scale by 32/20 = 1.6; 2.5 × 1.6 = 4 cups."),
        ],
    },
    {
        "key": "evidence",
        "title": "Command of evidence in short passages",
        "subject": "rw",
        "topic": "Information and Ideas · Evidence",
        "duration_minutes": 9,
        "summary": "Match claims to evidence by testing exactly what each choice proves.",
        "material": "Restate the claim in precise terms. For each option, ask whether the evidence directly supports every important part of that claim—not merely the passage’s general topic.",
        "progress_percent": 100,
        "is_today": False,
        "sort_order": 4,
        "homework_title": "Evidence and inference set",
        "homework_description": "Practice selecting evidence that directly supports a claim.",
        "deadline_days": -8,
        "questions": [
            ("A study found that seedlings under blue light grew taller than those under red light. Which claim is best supported?", "Blue light always improves plant health.", "Light color can affect seedling height.", "Red light prevents photosynthesis.", "All seedlings require blue light.", "B", "The data supports an effect on height, not broader claims about health or necessity."),
            ("A town added protected bike lanes; bicycle trips rose 18% the next year. Which inference is most reasonable?", "The lanes may have encouraged more cycling.", "Every resident now owns a bicycle.", "Car travel ended in the town.", "Cycling increased exactly 18% in every neighborhood.", "A", "The timing supports a cautious connection, while the other choices overstate the evidence."),
            ("Survey respondents who read daily reported higher vocabulary scores. What limitation matters most?", "The survey cannot by itself prove that reading caused the scores.", "Vocabulary cannot be measured.", "Daily readers never watch television.", "All surveys are inaccurate.", "A", "Correlation alone does not establish causation."),
            ("After insulation was installed, a building used 12% less heating energy. Which evidence would most strengthen the claim that insulation caused the decrease?", "The building is 20 years old.", "That winter was warmer than average.", "Similar nearby buildings without new insulation showed no decrease.", "The insulation was blue.", "C", "A comparison group helps rule out broader factors such as weather."),
        ],
    },
]


class Command(BaseCommand):
    help = "Create or refresh the idempotent Cereqo demo dataset."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete Cereqo demo data before reseeding.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            AttendanceSession.objects.all().delete()
            DemoConfig.objects.all().delete()
            Student.objects.all().delete()
            Lesson.objects.all().delete()

        today = timezone.localdate()
        now = timezone.now()
        DemoConfig.objects.update_or_create(
            name="Cereqo demo", defaults={"exam_date": today + timedelta(days=73)}
        )
        student_specs = [
            ("Noah Williams", "NW", 980, 14, "Consistency King", False),
            ("Priya Shah", "PS", 930, 9, "Word Wizard", False),
            ("Mateo Rivera", "MR", 875, 11, "Algebra Ace", False),
            ("Alex Morgan", "AM", 820, 6, "Momentum Maker", True),
            ("Sofia Chen", "SC", 790, 5, "Evidence Expert", False),
            ("Ethan Brooks", "EB", 735, 3, "Quick Starter", False),
        ]
        students = {}
        for name, initials, points, streak, badge, is_demo in student_specs:
            obj, _ = Student.objects.get_or_create(
                name=name,
                defaults={"initials": initials, "points": points, "streak": streak, "badge": badge, "is_demo": is_demo},
            )
            students[name] = obj
        Student.objects.filter(name="Alex Morgan").update(is_demo=True)
        Student.objects.exclude(name="Alex Morgan").update(is_demo=False)

        homeworks = {}
        for item in LESSONS:
            lesson, _ = Lesson.objects.update_or_create(
                title=item["title"],
                defaults={
                    "subject": item["subject"],
                    "topic": item["topic"],
                    "duration_minutes": item["duration_minutes"],
                    "summary": item["summary"],
                    "material": item["material"],
                    "progress_percent": item["progress_percent"],
                    "is_today": item["is_today"],
                    "sort_order": item["sort_order"],
                    "video_file": "cereqo/video/demo-lesson-video.mp4",
                },
            )
            deadline_date = today + timedelta(days=item["deadline_days"])
            deadline = timezone.make_aware(datetime.combine(deadline_date, time(20, 0)))
            homework, _ = Homework.objects.update_or_create(
                lesson=lesson,
                defaults={
                    "title": item["homework_title"],
                    "description": item["homework_description"],
                    "deadline": deadline,
                    "max_points": 100,
                    "sort_order": item["sort_order"],
                },
            )
            homeworks[item["key"]] = homework
            positions = []
            for position, values in enumerate(item["questions"], start=1):
                prompt, a, b, c, d, correct, explanation = values
                Question.objects.update_or_create(
                    homework=homework,
                    position=position,
                    defaults={
                        "prompt": prompt,
                        "option_a": a,
                        "option_b": b,
                        "option_c": c,
                        "option_d": d,
                        "correct_option": correct,
                        "explanation": explanation,
                    },
                )
                positions.append(position)
            homework.questions.exclude(position__in=positions).delete()

        demo_student = students["Alex Morgan"]
        in_progress, created = Submission.objects.get_or_create(student=demo_student, homework=homeworks["transitions"])
        if created:
            first = homeworks["transitions"].questions.first()
            Answer.objects.create(submission=in_progress, question=first, selected_option="B")

        completed, created = Submission.objects.get_or_create(student=demo_student, homework=homeworks["evidence"])
        if created:
            choices = ["B", "A", "A", "B"]
            for question, choice in zip(homeworks["evidence"].questions.all(), choices):
                Answer.objects.create(submission=completed, question=question, selected_option=choice)
            submitted_at = homeworks["evidence"].deadline + timedelta(hours=15)
            Submission.objects.filter(pk=completed.pk).update(
                started_at=submitted_at - timedelta(hours=2),
                submitted_at=submitted_at,
                score=75,
                points_awarded=75,
            )

        attendance_specs = [
            (-16, "Core algebra workshop", "Math", "attended", "Strong work translating constraints into equations."),
            (-11, "Rhetorical synthesis lab", "Reading & Writing", "attended", "Completed the source-matching challenge."),
            (-7, "Advanced math clinic", "Math", "missed", "Session recording and recap are available."),
            (-3, "Reading inference studio", "Reading & Writing", "attended", "Accurate evidence selection across both passages."),
            (2, "Linear equations review", "Math", "scheduled", "Bring your checkpoint questions."),
            (7, "Transitions and cohesion", "Reading & Writing", "scheduled", "Live guided practice and Q&A."),
        ]
        expected_attendance_dates = [today + timedelta(days=item[0]) for item in attendance_specs]
        AttendanceSession.objects.exclude(date__in=expected_attendance_dates).delete()
        for offset, title, subject, status, notes in attendance_specs:
            session_date = today + timedelta(days=offset)
            AttendanceSession.objects.update_or_create(
                date=session_date,
                defaults={"title": title, "subject": subject, "start_time": time(17, 30), "status": status, "notes": notes},
            )

        self.stdout.write(self.style.SUCCESS("Cereqo demo data is ready."))
