from datetime import datetime, time, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from learning.models import (
    Answer,
    AttendanceSession,
    Course,
    CourseEnrollment,
    CourseSection,
    DemoConfig,
    Homework,
    Lesson,
    Question,
    Student,
    Submission,
)


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


EXTRA_CHECKPOINTS = [
    {
        "key": "craft",
        "title": "Text structure and cross-text connections",
        "subject": "rw",
        "topic": "Craft and Structure",
        "duration_minutes": 9,
        "summary": "Read like a writer: track purpose, structure, and relationships across short texts.",
        "material": "Name the job of each sentence and paragraph. For paired texts, state each author’s position independently before comparing where they agree, differ, or qualify one another.",
        "progress_percent": 100,
        "homework_title": "Craft and Structure checkpoint",
        "homework_description": "A timed section review of vocabulary, purpose, structure, and paired-text reasoning.",
        "questions": [
            ("In context, the word ‘qualified’ most nearly means", "trained", "limited", "praised", "employed", "B", "A qualified claim is limited or made less absolute."),
            ("An author describes an old theory before presenting new evidence mainly to", "introduce a contrast", "define a technical term", "repeat the conclusion", "avoid a claim", "A", "The old theory establishes the position that the new evidence challenges."),
            ("Text 1 calls the policy effective; Text 2 says its effect is promising but not yet proven. Text 2 would most likely", "fully reject Text 1", "qualify Text 1’s conclusion", "discuss an unrelated issue", "provide the same certainty", "B", "Text 2 accepts the possibility but reduces the certainty of Text 1’s claim."),
        ],
    },
    {
        "key": "conventions",
        "title": "Form, structure, and sense",
        "subject": "rw",
        "topic": "Standard English Conventions",
        "duration_minutes": 8,
        "summary": "Edit sentence boundaries, agreement, and modifiers with repeatable grammar checks.",
        "material": "First identify complete clauses. Then choose punctuation based on the boundary between them. Finally, verify subject–verb agreement and place modifiers beside the words they describe.",
        "progress_percent": 76,
        "homework_title": "English Conventions checkpoint",
        "homework_description": "A section-ending grammar set covering boundaries, form, structure, and sense.",
        "questions": [
            ("The samples were stored at low temperature ___ the team analyzed them the next morning.", ",", ";", ": and", "because,", "B", "A semicolon correctly joins two closely related independent clauses."),
            ("The collection of maps ___ housed in a climate-controlled room.", "are", "were", "is", "have been", "C", "The subject is the singular noun ‘collection,’ so ‘is’ agrees."),
            ("Walking through the gallery, ___", "the sculptures impressed Mina", "Mina studied the sculptures", "the lights were bright", "there were many sculptures", "B", "Mina is the person walking, so she must immediately follow the modifier."),
        ],
    },
    {
        "key": "advanced",
        "title": "Nonlinear functions and equations",
        "subject": "math",
        "topic": "Advanced Math",
        "duration_minutes": 10,
        "summary": "Connect equivalent expressions, nonlinear equations, and their graphs.",
        "material": "Look for structure before expanding. Factoring reveals zeros, vertex form reveals a minimum or maximum, and exponential form reveals a constant percent change.",
        "progress_percent": 0,
        "homework_title": "Advanced Math checkpoint",
        "homework_description": "A timed review of equivalent expressions and nonlinear functions.",
        "questions": [
            ("Which expression is equivalent to x² − 9?", "(x − 9)(x + 1)", "(x − 3)(x + 3)", "(x − 3)²", "x(x − 9)", "B", "This is a difference of squares: x² − 3² = (x − 3)(x + 3)."),
            ("If 2ˣ = 32, what is x?", "4", "5", "8", "16", "B", "Since 32 = 2⁵, x = 5."),
            ("The graph of y = (x − 4)² + 2 has its minimum at", "(−4, 2)", "(2, 4)", "(4, 2)", "(4, −2)", "C", "Vertex form y = (x − h)² + k has vertex (h, k)."),
        ],
    },
    {
        "key": "geometry",
        "title": "Circles, area, and volume",
        "subject": "math",
        "topic": "Geometry and Trigonometry",
        "duration_minutes": 9,
        "summary": "Translate diagrams into relationships using geometry and trigonometry.",
        "material": "Mark known lengths and angles directly on the diagram. Choose a relationship only after naming the target: similarity, Pythagorean theorem, trigonometric ratio, circle property, area, or volume.",
        "progress_percent": 0,
        "homework_title": "Geometry and Trigonometry checkpoint",
        "homework_description": "The final domain checkpoint before the full adaptive simulation.",
        "questions": [
            ("A circle has radius 6. What is its area?", "6π", "12π", "24π", "36π", "D", "Area is πr² = π(6²) = 36π."),
            ("A right triangle has legs 5 and 12. Its hypotenuse is", "13", "15", "17", "25", "A", "By the Pythagorean theorem, √(5² + 12²) = √169 = 13."),
            ("A cylinder has radius 3 and height 4. What is its volume?", "12π", "24π", "36π", "48π", "C", "Volume is πr²h = π(3²)(4) = 36π."),
        ],
    },
]


SECTION_SPECS = [
    ("Information and Ideas", "Reading evidence and inference", "rw", -35, -29, 26, "evidence", "Central ideas and quantitative evidence"),
    ("Craft and Structure", "Words, purpose, and text connections", "rw", -28, -22, 28, "craft", "Words in context and author purpose"),
    ("Standard English Conventions", "Grammar and sentence boundaries", "rw", -21, -15, 26, "conventions", "Sentence boundaries and agreement"),
    ("Expression of Ideas", "Rhetorical synthesis and transitions", "rw", -14, -8, 20, "transitions", "Rhetorical synthesis from source notes"),
    ("Algebra", "Linear relationships and systems", "math", -7, 1, 34, "linear", "Linear functions and systems"),
    ("Advanced Math", "Equivalent expressions and nonlinear models", "math", 2, 6, 34, "advanced", "Equivalent expressions and quadratics"),
    ("Problem-Solving and Data Analysis", "Rates, percentages, and data", "math", 7, 13, 16, "ratios", "Percentages, distributions, and probability"),
    ("Geometry and Trigonometry", "Shapes, circles, and trigonometry", "math", 14, 20, 16, "geometry", "Triangles and trigonometric ratios"),
]


DEMO_COURSES = [
    {
        "code": "sat-math-accelerator",
        "title": "SAT Math Accelerator · 4-Week Path",
        "description": "A focused math course for linear models, nonlinear functions, data analysis, and geometry.",
        "start_offset": 7,
        "target_score": 760,
        "subject": "math",
        "instructor_name": "Aziz Rahmonov",
        "instructor_role": "SAT Math mentor",
        "cover_image": "cereqo/img/mentors/mentor-aziz.jpg",
        "domains": ["Algebra", "Advanced Math", "Problem-Solving and Data Analysis", "Geometry and Trigonometry"],
    },
    {
        "code": "sat-reading-writing-sprint",
        "title": "SAT Reading & Writing Sprint · 4-Week Path",
        "description": "A focused literacy course for evidence, vocabulary, grammar, synthesis, and transitions.",
        "start_offset": 14,
        "target_score": 720,
        "subject": "rw",
        "instructor_name": "Madina Karimova",
        "instructor_role": "Reading & Writing mentor",
        "cover_image": "cereqo/img/mentors/mentor-madina.jpg",
        "domains": ["Information and Ideas", "Craft and Structure", "Standard English Conventions", "Expression of Ideas"],
    },
]


INDEPENDENT_TASKS = [
    {
        "key": "vocabulary",
        "title": "Weekly SAT vocabulary challenge",
        "description": "Use context clues to choose precise meanings in a short mentor-assigned set.",
        "subject": "rw",
        "assigned_by": "Madina Karimova",
        "deadline_days": 3,
        "questions": [
            ("In the passage, ‘novel’ most nearly means", "lengthy", "original", "fictional", "uncertain", "B", "Here ‘novel’ describes an original approach, not a type of book."),
            ("Which word best completes a sentence describing a careful and exact method?", "random", "meticulous", "brief", "casual", "B", "‘Meticulous’ means very careful and precise."),
        ],
    },
    {
        "key": "speed",
        "title": "Mixed Math speed drill",
        "description": "Complete a compact mixed set while keeping each decision under ninety seconds.",
        "subject": "math",
        "assigned_by": "Aziz Rahmonov",
        "deadline_days": 1,
        "questions": [
            ("If 3x + 5 = 20, what is x?", "3", "5", "7", "15", "B", "Subtract 5, then divide 15 by 3 to get 5."),
            ("What is 15% of 80?", "8", "10", "12", "15", "C", "0.15 × 80 = 12."),
        ],
    },
    {
        "key": "accuracy",
        "title": "Evidence accuracy clinic",
        "description": "Review claim-and-evidence choices and identify the exact reason each distractor fails.",
        "subject": "rw",
        "assigned_by": "Cereqo academic team",
        "deadline_days": -2,
        "questions": [
            ("The strongest evidence for a claim should be", "broadly related", "specific and directly relevant", "the longest option", "an unsupported opinion", "B", "Strong evidence directly supports the precise claim."),
            ("Which choice weakens an inference most?", "A relevant comparison", "A repeated detail", "A credible alternative explanation", "A precise measurement", "C", "A credible alternative explanation makes the original inference less certain."),
        ],
    },
    {
        "key": "diagnostic",
        "title": "Diagnostic mini set",
        "description": "A brief mixed diagnostic used by your mentor to plan the next coaching session.",
        "subject": "math",
        "assigned_by": "Daniel Brooks",
        "deadline_days": -5,
        "questions": [
            ("A line has slope 2 and passes through (0, 3). Which equation represents it?", "y = 2x + 3", "y = 3x + 2", "y = 2x − 3", "y = x + 5", "A", "Slope-intercept form is y = mx + b, so y = 2x + 3."),
            ("If x² = 49 and x is positive, what is x?", "5", "6", "7", "9", "C", "The positive square root of 49 is 7."),
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
            Homework.objects.filter(kind=Homework.INDEPENDENT).delete()
            DemoConfig.objects.all().delete()
            Student.objects.all().delete()
            Course.objects.all().delete()
            Lesson.objects.all().delete()

        today = timezone.localdate()
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

        demo_user, _ = get_user_model().objects.get_or_create(
            username=settings.DEMO_LOGIN_USERNAME,
            defaults={
                "email": "demo@cereqo.uz",
                "first_name": "Alex",
                "last_name": "Morgan",
            },
        )
        demo_user.email = "demo@cereqo.uz"
        demo_user.first_name = "Alex"
        demo_user.last_name = "Morgan"
        demo_user.set_password(settings.DEMO_LOGIN_PASSWORD)
        demo_user.save()
        demo_student = students["Alex Morgan"]
        if demo_student.user_id != demo_user.pk:
            demo_student.user = demo_user
            demo_student.save(update_fields=["user"])

        course, _ = Course.objects.update_or_create(
            code="digital-sat-mastery",
            defaults={
                "title": "Digital SAT Mastery · 8-Week Path",
                "description": "A domain-by-domain path built around the official digital SAT structure, timed practice, review, and section checkpoints.",
                "instructor_name": "Daniel Brooks",
                "instructor_role": "SAT strategy lead",
                "cover_image": "cereqo/img/mentors/cereqo-classroom.jpg",
                "start_date": today - timedelta(days=35),
                "end_date": today + timedelta(days=20),
                "target_score": 1400,
                "is_active": True,
            },
        )
        Course.objects.exclude(pk=course.pk).update(is_active=False)
        CourseEnrollment.objects.get_or_create(student=demo_student, course=course)

        checkpoint_specs = {item["key"]: item for item in [*LESSONS, *EXTRA_CHECKPOINTS]}
        homeworks = {}
        course_lessons = []
        sections = []
        for order, section_spec in enumerate(SECTION_SPECS, start=1):
            domain, title, subject, start_offset, end_offset, weight, checkpoint_key, intro_title = section_spec
            section, _ = CourseSection.objects.update_or_create(
                course=course,
                order=order,
                defaults={
                    "title": title,
                    "domain": domain,
                    "subject": subject,
                    "description": f"Build the core {domain} skills, then prove mastery in a timed checkpoint.",
                    "start_date": today + timedelta(days=start_offset),
                    "end_date": today + timedelta(days=end_offset),
                    "exam_weight_percent": weight,
                },
            )
            sections.append(section)

            intro_progress = 100 if start_offset <= 0 else 0
            intro_lesson, _ = Lesson.objects.update_or_create(
                title=intro_title,
                defaults={
                    "section": section,
                    "subject": subject,
                    "topic": f"{domain} · Core skill",
                    "duration_minutes": 8,
                    "session_minutes": 75,
                    "summary": f"Learn the essential patterns and decision process for {domain} questions.",
                    "material": "Start with a short concept model, work through a guided example, then solve a timed mini-set. Finish by logging the error type and the fastest reliable correction.",
                    "progress_percent": intro_progress,
                    "is_today": False,
                    "scheduled_date": today + timedelta(days=start_offset),
                    "sequence": 1,
                    "sort_order": order * 10 + 1,
                    "video_file": "cereqo/video/demo-lesson-video.mp4",
                },
            )
            course_lessons.append(intro_lesson)

            item = checkpoint_specs[checkpoint_key]
            checkpoint_date = today + timedelta(days=end_offset - 1)
            lesson, _ = Lesson.objects.update_or_create(
                title=item["title"],
                defaults={
                    "section": section,
                    "subject": item["subject"],
                    "topic": item["topic"],
                    "duration_minutes": item["duration_minutes"],
                    "session_minutes": 75,
                    "summary": item["summary"],
                    "material": item["material"],
                    "progress_percent": item["progress_percent"],
                    "is_today": checkpoint_date == today,
                    "scheduled_date": checkpoint_date,
                    "sequence": 2,
                    "sort_order": order * 10 + 2,
                    "video_file": "cereqo/video/demo-lesson-video.mp4",
                },
            )
            course_lessons.append(lesson)

            deadline_date = today + timedelta(days=end_offset + 1)
            deadline = timezone.make_aware(datetime.combine(deadline_date, time(20, 0)))
            homework, _ = Homework.objects.get_or_create(
                lesson=lesson,
                defaults={
                    "title": item["homework_title"],
                    "description": item["homework_description"],
                    "deadline": deadline,
                },
            )
            homework.section = section
            homework.kind = Homework.COURSE
            homework.subject = lesson.subject
            homework.assigned_by = course.instructor_name
            homework.title = item["homework_title"]
            homework.description = item["homework_description"]
            homework.deadline = deadline
            homework.max_points = 100
            homework.sort_order = order
            homework.save()
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

        CourseSection.objects.filter(course=course).exclude(pk__in=[item.pk for item in sections]).delete()

        for demo_spec in DEMO_COURSES:
            demo_start = today + timedelta(days=demo_spec["start_offset"])
            demo_course, _ = Course.objects.update_or_create(
                code=demo_spec["code"],
                defaults={
                    "title": demo_spec["title"],
                    "description": demo_spec["description"],
                    "instructor_name": demo_spec["instructor_name"],
                    "instructor_role": demo_spec["instructor_role"],
                    "cover_image": demo_spec["cover_image"],
                    "start_date": demo_start,
                    "end_date": demo_start + timedelta(days=27),
                    "target_score": demo_spec["target_score"],
                    "is_active": False,
                },
            )
            demo_section_ids = []
            for demo_order, domain in enumerate(demo_spec["domains"], start=1):
                section_start = demo_start + timedelta(days=(demo_order - 1) * 7)
                demo_section, _ = CourseSection.objects.update_or_create(
                    course=demo_course,
                    order=demo_order,
                    defaults={
                        "title": f"{domain} intensive",
                        "domain": domain,
                        "subject": demo_spec["subject"],
                        "description": f"Build speed and accuracy across the highest-value {domain} skills.",
                        "start_date": section_start,
                        "end_date": section_start + timedelta(days=6),
                        "exam_weight_percent": 25,
                    },
                )
                demo_section_ids.append(demo_section.pk)
                for sequence, suffix in ((1, "Strategy lab"), (2, "Timed practice")):
                    demo_lesson, _ = Lesson.objects.update_or_create(
                        section=demo_section,
                        sequence=sequence,
                        defaults={
                            "title": f"{domain} · {suffix}",
                            "section": demo_section,
                            "subject": demo_spec["subject"],
                            "topic": domain,
                            "duration_minutes": 8,
                            "session_minutes": 75,
                            "summary": f"A focused {domain} session built around repeatable SAT decisions.",
                            "material": "Model the skill, complete guided examples, solve a timed set, and classify every error before moving on.",
                            "progress_percent": 0,
                            "is_today": False,
                            "scheduled_date": section_start + timedelta(days=sequence * 2 - 2),
                            "sort_order": 1000 + demo_order * 10 + sequence,
                            "video_file": "cereqo/video/demo-lesson-video.mp4",
                        },
                    )
                    if sequence == 2:
                        demo_deadline = timezone.make_aware(
                            datetime.combine(demo_section.end_date + timedelta(days=1), time(20, 0))
                        )
                        demo_homework, _ = Homework.objects.get_or_create(
                            lesson=demo_lesson,
                            defaults={
                                "title": f"{domain} final test",
                                "description": f"Section mastery test for {domain}.",
                                "deadline": demo_deadline,
                            },
                        )
                        demo_homework.section = demo_section
                        demo_homework.kind = Homework.COURSE
                        demo_homework.subject = demo_lesson.subject
                        demo_homework.assigned_by = demo_course.instructor_name
                        demo_homework.title = f"{domain} final test"
                        demo_homework.description = f"Section mastery test for {domain}."
                        demo_homework.deadline = demo_deadline
                        demo_homework.max_points = 100
                        demo_homework.sort_order = 100 + demo_order
                        demo_homework.save()
                        demo_questions = (
                            [
                                ("If 4x + 3 = 19, what is x?", "2", "3", "4", "5", "C", "Subtract 3, then divide 16 by 4."),
                                ("A value increases from 40 to 50. What is the percent increase?", "10%", "20%", "25%", "40%", "C", "The increase is 10, and 10/40 = 25%."),
                            ]
                            if demo_spec["subject"] == "math"
                            else [
                                ("Which transition best signals a contrast?", "Therefore", "However", "For example", "Similarly", "B", "‘However’ signals contrast."),
                                ("Which choice most directly supports a claim?", "A related opinion", "A repeated topic", "Specific relevant evidence", "A broad assumption", "C", "Direct, relevant evidence best supports a claim."),
                            ]
                        )
                        for position, values in enumerate(demo_questions, start=1):
                            prompt, a, b, c, d, correct, explanation = values
                            Question.objects.update_or_create(
                                homework=demo_homework,
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
                        demo_homework.questions.exclude(position__in=[1, 2]).delete()
            CourseSection.objects.filter(course=demo_course).exclude(pk__in=demo_section_ids).delete()

        independent_homeworks = {}
        independent_titles = []
        for order, item in enumerate(INDEPENDENT_TASKS, start=1):
            deadline = timezone.make_aware(
                datetime.combine(today + timedelta(days=item["deadline_days"]), time(20, 0))
            )
            homework, _ = Homework.objects.update_or_create(
                kind=Homework.INDEPENDENT,
                title=item["title"],
                defaults={
                    "lesson": None,
                    "section": None,
                    "subject": item["subject"],
                    "assigned_by": item["assigned_by"],
                    "description": item["description"],
                    "deadline": deadline,
                    "max_points": 60,
                    "sort_order": order,
                },
            )
            independent_titles.append(item["title"])
            independent_homeworks[item["key"]] = homework
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
            homework.questions.exclude(position__in=range(1, len(item["questions"]) + 1)).delete()
        Homework.objects.filter(kind=Homework.INDEPENDENT).exclude(title__in=independent_titles).delete()

        independent_progress, created = Submission.objects.get_or_create(
            student=demo_student, homework=independent_homeworks["speed"]
        )
        if created:
            first = independent_homeworks["speed"].questions.first()
            Answer.objects.create(submission=independent_progress, question=first, selected_option="B")

        independent_completed, created = Submission.objects.get_or_create(
            student=demo_student, homework=independent_homeworks["diagnostic"]
        )
        if created:
            for question in independent_homeworks["diagnostic"].questions.all():
                Answer.objects.create(
                    submission=independent_completed,
                    question=question,
                    selected_option=question.correct_option,
                )
            submitted_at = independent_homeworks["diagnostic"].deadline - timedelta(hours=2)
            Submission.objects.filter(pk=independent_completed.pk).update(
                started_at=submitted_at - timedelta(minutes=20),
                submitted_at=submitted_at,
                score=100,
                points_awarded=60,
            )

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

        old_demo_titles = [
            "Core algebra workshop",
            "Rhetorical synthesis lab",
            "Advanced math clinic",
            "Reading inference studio",
            "Linear equations review",
            "Transitions and cohesion",
        ]
        AttendanceSession.objects.filter(lesson__section__course=course).delete()
        AttendanceSession.objects.filter(title__in=old_demo_titles).delete()
        for lesson in course_lessons:
            session_date = lesson.scheduled_date
            if session_date < today:
                status = "missed" if lesson.section.order == 3 and lesson.sequence == 2 else "attended"
            else:
                status = "scheduled"
            subject_label = "Math" if lesson.subject == "math" else "Reading & Writing"
            notes = (
                "Review the recording and complete the section checkpoint."
                if status == "missed"
                else "Concept model, guided practice, timed set, and error-log review."
            )
            AttendanceSession.objects.update_or_create(
                date=session_date,
                defaults={
                    "lesson": lesson,
                    "title": lesson.title,
                    "subject": subject_label,
                    "start_time": time(17, 30),
                    "status": status,
                    "notes": notes,
                },
            )

        self.stdout.write(self.style.SUCCESS("Cereqo demo data is ready."))
