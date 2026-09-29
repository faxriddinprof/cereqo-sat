import json

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.management import call_command
from django.db.models import Q
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from .models import (
    Answer,
    AttendanceSession,
    Course,
    CourseEnrollment,
    CourseSection,
    Homework,
    Lesson,
    Student,
    Submission,
)


class DemoFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def setUp(self):
        self.student = Student.objects.get(is_demo=True)
        self.user = get_user_model().objects.get(username=settings.DEMO_LOGIN_USERNAME)
        self.client.force_login(self.user)

    def test_seed_is_idempotent(self):
        before = {
            "students": Student.objects.count(),
            "lessons": Lesson.objects.count(),
            "homework": Homework.objects.count(),
            "attendance": AttendanceSession.objects.count(),
            "courses": Course.objects.count(),
            "enrollments": CourseEnrollment.objects.count(),
            "sections": CourseSection.objects.count(),
        }
        call_command("seed_demo", verbosity=0)
        self.assertEqual(before["students"], Student.objects.count())
        self.assertEqual(before["lessons"], Lesson.objects.count())
        self.assertEqual(before["homework"], Homework.objects.count())
        self.assertEqual(before["attendance"], AttendanceSession.objects.count())
        self.assertEqual(before["courses"], Course.objects.count())
        self.assertEqual(before["enrollments"], CourseEnrollment.objects.count())
        self.assertEqual(before["sections"], CourseSection.objects.count())

    def test_course_uses_all_official_domains_in_order(self):
        self.assertEqual(Course.objects.count(), 3)
        course = Course.objects.get(is_active=True)
        self.assertEqual(course.instructor_name, "Daniel Brooks")
        self.assertTrue(course.cover_image.startswith("cereqo/img/mentors/"))
        self.assertEqual(course.sections.count(), 8)
        self.assertEqual(Lesson.objects.filter(section__course=course).count(), 16)
        self.assertEqual(
            list(course.sections.values_list("domain", flat=True)),
            [
                "Information and Ideas",
                "Craft and Structure",
                "Standard English Conventions",
                "Expression of Ideas",
                "Algebra",
                "Advanced Math",
                "Problem-Solving and Data Analysis",
                "Geometry and Trigonometry",
            ],
        )

    def test_every_course_has_its_own_instructor_and_cover(self):
        courses = list(Course.objects.all())
        self.assertEqual(len({course.instructor_name for course in courses}), len(courses))
        for course in courses:
            self.assertTrue(course.instructor_role)
            self.assertTrue(course.cover_image)

    def test_authenticated_course_catalog_separates_my_courses(self):
        self.client.post(reverse("set_language"), {"language": "en", "next": "/learn/"})
        page = self.client.get(reverse("learning:learn"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "My courses")
        self.assertEqual(len(page.context["my_course_cards"]), 1)
        self.assertEqual(page.context["my_course_cards"][0]["course"].code, "digital-sat-mastery")
        self.assertEqual(len(page.context["course_cards"]), 2)
        self.assertNotContains(page, "1400+")
        self.assertNotContains(page, "course-system-note")

    def test_homepage_rotates_courses_without_duplicate_course_section(self):
        page = self.client.get(reverse("learning:dashboard"))
        self.assertContains(page, 'id="courseHero"')
        self.assertContains(page, "carousel-fade")
        self.assertContains(page, 'class="carousel-item', count=3)
        self.assertContains(page, 'class="course-hero-media"', count=3)
        self.assertNotContains(page, "hero-score-card")
        self.assertNotContains(page, "minimal-courses")
        self.assertNotContains(page, "minimal-trust")
        self.assertContains(page, 'class="landing-section platform-showcase"')
        self.assertContains(page, 'class="mentor-showcase-card', count=3)
        self.assertContains(page, 'class="homepage-final-cta"')

    def test_each_section_ends_with_its_checkpoint(self):
        for section in CourseSection.objects.prefetch_related("lessons"):
            self.assertEqual(section.lessons.count(), 2)
            self.assertEqual(section.checkpoint.lesson, section.lessons.order_by("sequence").last())
            self.assertGreater(section.checkpoint.questions.count(), 0)
            self.assertGreater(section.checkpoint.deadline.date(), section.end_date)

    def test_calendar_sessions_are_generated_from_course_lessons(self):
        course = Course.objects.get(is_active=True)
        lessons = Lesson.objects.filter(section__course=course)
        self.assertEqual(AttendanceSession.objects.filter(lesson__in=lessons).count(), lessons.count())
        for session in AttendanceSession.objects.select_related("lesson"):
            self.assertEqual(session.date, session.lesson.scheduled_date)

    def test_course_section_and_calendar_pages_render(self):
        self.client.post(reverse("set_language"), {"language": "en", "next": "/learn/"})
        with translation.override("en"):
            course_page = self.client.get(reverse("learning:learn"))
            self.assertContains(course_page, "Digital SAT Mastery")
            self.assertContains(course_page, "SAT Math Accelerator")
            self.assertNotContains(course_page, "courses-heading")
            self.assertNotContains(course_page, "courses-blueprint")
            course = Course.objects.get(is_active=True)
            course_detail = self.client.get(reverse("learning:course_detail", args=[course.pk]))
            self.assertContains(course_detail, 'class="course-overview-media"')
            self.assertContains(course_detail, 'class="course-section-tile section-state-', count=8)
            self.assertContains(course_detail, "Final checkpoint")
            self.assertNotContains(course_detail, 'class="course-sidebar"')
            self.assertNotContains(course_detail, "sat-blueprint")
            self.assertNotContains(course_detail, "lesson-rhythm")
            section = CourseSection.objects.first()
            section_page = self.client.get(reverse("learning:section_detail", args=[section.pk]))
            self.assertContains(section_page, section.title)
            self.assertContains(section_page, 'class="course-sidebar"')
            calendar_page = self.client.get(reverse("learning:attendance"))
            self.assertContains(calendar_page, "Learning calendar")
            profile_page = self.client.get(reverse("learning:profile"))
            self.assertContains(profile_page, "Learner profile")

    def test_profile_is_reached_from_avatar_menu_not_main_navigation(self):
        dashboard = self.client.get(reverse("learning:dashboard"))
        self.assertContains(dashboard, reverse("learning:profile"))
        self.assertContains(dashboard, 'class="dropdown profile-menu"')
        self.assertNotContains(dashboard, '<nav class="desktop-main-nav" aria-label="Main navigation"><a href="/profile/"')

    def test_initial_data_exposes_all_four_computed_states(self):
        states = {
            homework.status_for(self.student)
            for homework in Homework.objects.filter(kind=Homework.INDEPENDENT)
        }
        self.assertEqual(states, {"not_started", "in_progress", "overdue", "completed"})

    def test_tasks_page_only_lists_independent_assignments(self):
        self.client.post(reverse("set_language"), {"language": "en", "next": "/homework/"})
        with translation.override("en"):
            page = self.client.get(reverse("learning:homework_list"))
            self.assertEqual(page.status_code, 200)
            self.assertEqual(len(page.context["cards"]), 4)
            self.assertTrue(
                all(card["homework"].kind == Homework.INDEPENDENT for card in page.context["cards"])
            )
            self.assertContains(page, "Weekly SAT vocabulary challenge")
            self.assertNotContains(page, "Linear equations checkpoint")
            self.assertContains(page, "outside a course")

    def test_schedule_combines_lessons_and_all_task_deadlines(self):
        page = self.client.get(reverse("learning:attendance"))
        self.assertEqual(page.status_code, 200)
        self.assertEqual(
            page.context["task_counts"]["total"],
            Homework.objects.filter(
                Q(kind=Homework.INDEPENDENT)
                | Q(kind=Homework.COURSE, section__course__enrollments__student=self.student),
                deadline__date__year=page.context["year"],
                deadline__date__month=page.context["month"],
            ).distinct().count(),
        )
        self.assertGreater(page.context["task_counts"]["independent"], 0)
        self.assertGreater(page.context["task_counts"]["course"], 0)
        self.assertContains(page, "task-marker")

    def test_independent_task_detail_has_no_course_sidebar(self):
        homework = Homework.objects.filter(kind=Homework.INDEPENDENT).first()
        page = self.client.get(reverse("learning:homework_detail", args=[homework.pk]))
        self.assertEqual(page.status_code, 200)
        self.assertIsNone(page.context["course_navigation"])
        self.assertNotContains(page, 'class="course-sidebar"')

    def test_autosave_persists_answer_for_resume(self):
        homework = Homework.objects.get(lesson__is_today=True)
        question = homework.questions.first()
        response = self.client.post(
            reverse("learning:autosave_answer", args=[homework.pk]),
            data=json.dumps({"question_id": question.pk, "selected_option": "A"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        submission = Submission.objects.get(student=self.student, homework=homework)
        self.assertEqual(Answer.objects.get(submission=submission, question=question).selected_option, "A")
        page = self.client.get(reverse("learning:homework_detail", args=[homework.pk]))
        self.assertContains(page, 'value="A" data-question-id="%s" checked' % question.pk)

    def test_submission_scores_and_awards_points_only_once(self):
        homework = Homework.objects.get(lesson__is_today=True)
        answers = {f"question_{q.pk}": q.correct_option for q in homework.questions.all()}
        answers["action"] = "submit"
        starting_points = self.student.points

        response = self.client.post(reverse("learning:homework_detail", args=[homework.pk]), answers)
        self.assertRedirects(response, reverse("learning:homework_detail", args=[homework.pk]))
        submission = Submission.objects.get(student=self.student, homework=homework)
        self.student.refresh_from_db()
        self.assertEqual(submission.score, 100)
        self.assertEqual(submission.points_awarded, homework.max_points)
        self.assertEqual(self.student.points, starting_points + homework.max_points)

        self.client.post(reverse("learning:homework_detail", args=[homework.pk]), answers)
        self.student.refresh_from_db()
        self.assertEqual(self.student.points, starting_points + homework.max_points)

    def test_submission_does_not_change_attendance(self):
        homework = Homework.objects.get(lesson__is_today=True)
        before = list(AttendanceSession.objects.values_list("pk", "status"))
        answers = {f"question_{q.pk}": q.correct_option for q in homework.questions.all()}
        answers["action"] = "submit"
        self.client.post(reverse("learning:homework_detail", args=[homework.pk]), answers)
        self.assertEqual(before, list(AttendanceSession.objects.values_list("pk", "status")))

    def test_profile_and_leaderboard_use_same_student(self):
        profile = self.client.get(reverse("learning:profile"))
        leaderboard = self.client.get(reverse("learning:leaderboard"))
        self.assertEqual(profile.context["student"], self.student)
        self.assertEqual(leaderboard.context["current_student"].rank, self.student.rank)

    def test_completed_late_work_stays_completed(self):
        homework = Homework.objects.get(lesson__title__startswith="Command of evidence")
        submission = homework.submission_for(self.student)
        self.assertTrue(submission.is_late)
        self.assertEqual(homework.status_for(self.student), "completed")

    def test_language_switch_persists_and_translates_dashboard(self):
        response = self.client.post(reverse("set_language"), {"language": "uz", "next": "/"})
        self.assertRedirects(response, "/")
        dashboard = self.client.get(reverse("learning:dashboard"))
        self.assertContains(dashboard, "Digital SAT Mastery · 8 haftalik yo‘l")
        self.assertContains(dashboard, ">UZ<")

        self.client.post(reverse("set_language"), {"language": "en", "next": "/"})
        dashboard = self.client.get(reverse("learning:dashboard"))
        self.assertContains(dashboard, "Digital SAT Mastery · 8-Week Path")

    def test_guest_can_only_open_home_courses_and_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("learning:dashboard")).status_code, 200)
        courses = self.client.get(reverse("learning:learn"))
        self.assertEqual(courses.status_code, 200)
        first_course_url = reverse("learning:course_detail", args=[Course.objects.first().pk])
        self.assertContains(courses, f'href="{first_course_url}"')
        self.assertNotContains(courses, "Boshlash uchun tizimga kiring")
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)

        private_urls = [
            reverse("learning:course_detail", args=[Course.objects.first().pk]),
            reverse("learning:homework_list"),
            reverse("learning:leaderboard"),
            reverse("learning:attendance"),
            reverse("learning:profile"),
        ]
        for url in private_urls:
            response = self.client.get(url)
            self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_navigation_expands_after_login(self):
        authenticated = self.client.get(reverse("learning:dashboard"))
        self.assertContains(authenticated, reverse("learning:homework_list"))
        self.assertContains(authenticated, reverse("learning:leaderboard"))

        self.client.logout()
        guest = self.client.get(reverse("learning:dashboard"))
        self.assertNotContains(guest, reverse("learning:homework_list"))
        self.assertNotContains(guest, reverse("learning:leaderboard"))
        self.assertContains(guest, reverse("login"))

    def test_demo_username_and_password_login(self):
        self.client.logout()
        response = self.client.post(
            reverse("login"),
            {
                "username": settings.DEMO_LOGIN_USERNAME,
                "password": settings.DEMO_LOGIN_PASSWORD,
            },
        )
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)
        self.assertEqual(self.client.get(reverse("learning:profile")).status_code, 200)
