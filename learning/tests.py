import json

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from .models import Answer, AttendanceSession, Course, CourseSection, Homework, Lesson, Student, Submission


class DemoFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def setUp(self):
        self.student = Student.objects.get(is_demo=True)

    def test_seed_is_idempotent(self):
        before = {
            "students": Student.objects.count(),
            "lessons": Lesson.objects.count(),
            "homework": Homework.objects.count(),
            "attendance": AttendanceSession.objects.count(),
            "courses": Course.objects.count(),
            "sections": CourseSection.objects.count(),
        }
        call_command("seed_demo", verbosity=0)
        self.assertEqual(before["students"], Student.objects.count())
        self.assertEqual(before["lessons"], Lesson.objects.count())
        self.assertEqual(before["homework"], Homework.objects.count())
        self.assertEqual(before["attendance"], AttendanceSession.objects.count())
        self.assertEqual(before["courses"], Course.objects.count())
        self.assertEqual(before["sections"], CourseSection.objects.count())

    def test_course_uses_all_official_domains_in_order(self):
        course = Course.objects.get(is_active=True)
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
            self.assertContains(course_page, "54")
            section = CourseSection.objects.first()
            section_page = self.client.get(reverse("learning:section_detail", args=[section.pk]))
            self.assertContains(section_page, section.title)
            calendar_page = self.client.get(reverse("learning:attendance"))
            self.assertContains(calendar_page, "Course calendar")

    def test_initial_data_exposes_all_four_computed_states(self):
        states = {homework.status_for(self.student) for homework in Homework.objects.all()}
        self.assertEqual(states, {"not_started", "in_progress", "overdue", "completed"})

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

    def test_dashboard_and_leaderboard_use_same_rank(self):
        dashboard = self.client.get(reverse("learning:dashboard"))
        leaderboard = self.client.get(reverse("learning:leaderboard"))
        self.assertEqual(dashboard.context["rank"], self.student.rank)
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
        self.assertContains(dashboard, "Keyingi qadamga tayyormisiz?")
        self.assertContains(dashboard, ">UZ<")

        self.client.post(reverse("set_language"), {"language": "en", "next": "/"})
        dashboard = self.client.get(reverse("learning:dashboard"))
        self.assertContains(dashboard, "Ready for your next step?")
