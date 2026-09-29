import calendar
import json
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .models import (
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
from .student_profiles import student_for_user


def _student(request):
    return student_for_user(request.user)


def _homework_cards(student, kind=Homework.INDEPENDENT):
    cards = []
    today = timezone.localdate()
    for homework in Homework.objects.filter(kind=kind).select_related(
        "lesson", "section", "section__course"
    ).prefetch_related("submissions__answers", "questions"):
        submission = homework.submission_for(student)
        status = homework.status_for(student)
        due_date = timezone.localdate(homework.deadline)
        days_until_due = (due_date - today).days
        cards.append(
            {
                "homework": homework,
                "submission": submission,
                "status": status,
                "answered": submission.answers.count() if submission else 0,
                "total": homework.questions.count(),
                "days_until_due": days_until_due,
                "deadline_tone": (
                    "complete" if status == "completed"
                    else "overdue" if days_until_due < 0
                    else "urgent" if days_until_due <= 2
                    else "upcoming"
                ),
            }
        )
    return cards


def _course_section_cards(course, student):
    sections = course.sections.prefetch_related(
        "lessons", "checkpoint__submissions__answers", "checkpoint__questions"
    )
    cards = []
    for section in sections:
        checkpoint = getattr(section, "checkpoint", None)
        cards.append(
            {
                "section": section,
                "lessons": list(section.lessons.all()),
                "status": section.status_for(student),
                "progress": section.progress_percent,
                "checkpoint": checkpoint,
                "checkpoint_status": checkpoint.status_for(student) if checkpoint else None,
            }
        )
    return cards


def _course_navigation(course, student, active_section_id=None, active_lesson_id=None, active_homework_id=None):
    return {
        "course": course,
        "progress": course.progress_percent,
        "sections": _course_section_cards(course, student),
        "active_section_id": active_section_id,
        "active_lesson_id": active_lesson_id,
        "active_homework_id": active_homework_id,
    }


def _course_cards(courses=None):
    cards = []
    courses = courses if courses is not None else Course.objects.all()
    for course in courses.prefetch_related("sections__lessons"):
        lessons = Lesson.objects.filter(section__course=course)
        cards.append(
            {
                "course": course,
                "progress": course.progress_percent,
                "sections": course.sections.count(),
                "lessons": lessons.count(),
                "completed_lessons": lessons.filter(progress_percent=100).count(),
                "status": "active" if course.is_active else "upcoming",
            }
        )
    return cards


def dashboard(request):
    return render(
        request,
        "learning/dashboard.html",
        {
            "landing_page": True,
            "active_nav": "home",
            "course_cards": _course_cards()[:3],
        },
    )


def learn(request):
    if not Course.objects.exists():
        return render(request, "learning/empty.html", {"active_nav": "learn"})
    all_courses = Course.objects.all()
    my_course_cards = []
    if request.user.is_authenticated:
        student = _student(request)
        enrolled_course_ids = CourseEnrollment.objects.filter(student=student).values_list(
            "course_id", flat=True
        )
        my_course_cards = _course_cards(all_courses.filter(pk__in=enrolled_course_ids))
        all_courses = all_courses.exclude(pk__in=enrolled_course_ids)
    return render(
        request,
        "learning/course_list.html",
        {
            "active_nav": "learn",
            "my_course_cards": my_course_cards,
            "course_cards": _course_cards(all_courses),
        },
    )


@login_required
def course_detail(request, course_id):
    student = _student(request)
    course = get_object_or_404(Course, pk=course_id)
    section_cards = _course_section_cards(course, student)
    course_lessons = Lesson.objects.filter(section__course=course)
    next_lesson = (
        course_lessons.filter(scheduled_date__gte=timezone.localdate())
        .order_by("scheduled_date", "sort_order")
        .first()
        or course_lessons.last()
    )
    return render(
        request,
        "learning/course_overview.html",
        {
            "active_nav": "learn",
            "course": course,
            "section_cards": section_cards,
            "next_lesson": next_lesson,
            "course_progress": course.progress_percent,
            "total_lessons": course_lessons.count(),
            "completed_lessons": course_lessons.filter(progress_percent=100).count(),
        },
    )


@login_required
def section_detail(request, section_id):
    student = _student(request)
    section = get_object_or_404(
        CourseSection.objects.select_related("course").prefetch_related("lessons", "checkpoint__questions"),
        pk=section_id,
    )
    checkpoint = getattr(section, "checkpoint", None)
    previous_section = section.course.sections.filter(order__lt=section.order).order_by("-order").first()
    next_section = section.course.sections.filter(order__gt=section.order).order_by("order").first()
    return render(
        request,
        "learning/section_detail.html",
        {
            "active_nav": "learn",
            "section": section,
            "lessons": section.lessons.all(),
            "checkpoint": checkpoint,
            "checkpoint_status": checkpoint.status_for(student) if checkpoint else None,
            "section_status": section.status_for(student),
            "previous_section": previous_section,
            "next_section": next_section,
            "course_navigation": _course_navigation(
                section.course, student, active_section_id=section.pk
            ),
        },
    )


@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related("section__course"), pk=lesson_id)
    homework = getattr(lesson, "homework", None)
    other_lessons = (
        Lesson.objects.filter(section=lesson.section).exclude(pk=lesson.pk)
        if lesson.section_id
        else Lesson.objects.exclude(pk=lesson.pk)[:3]
    )
    return render(
        request,
        "learning/lesson_detail.html",
        {
            "active_nav": "learn",
            "lesson": lesson,
            "homework": homework,
            "other_lessons": other_lessons,
            "course_navigation": _course_navigation(
                lesson.section.course,
                _student(request),
                active_section_id=lesson.section_id,
                active_lesson_id=lesson.pk,
            ) if lesson.section_id else None,
        },
    )


@login_required
def homework_list(request):
    student = _student(request)
    cards = _homework_cards(student)
    counts = {key: sum(card["status"] == key for card in cards) for key in ("not_started", "in_progress", "overdue", "completed")}
    return render(
        request,
        "learning/homework_list.html",
        {"active_nav": "tasks", "cards": cards, "counts": counts},
    )


@login_required
def homework_detail(request, homework_id):
    student = _student(request)
    homework = get_object_or_404(Homework.objects.select_related("lesson", "section", "section__course"), pk=homework_id)
    submission, created = Submission.objects.get_or_create(student=student, homework=homework)
    questions = list(homework.questions.all())

    if request.method == "POST" and not submission.submitted_at:
        for question in questions:
            selected = request.POST.get(f"question_{question.pk}")
            if selected in dict(Question.OPTION_CHOICES):
                Answer.objects.update_or_create(
                    submission=submission, question=question, defaults={"selected_option": selected}
                )
        if request.POST.get("action") == "submit":
            answered_count = submission.answers.count()
            if answered_count != len(questions):
                messages.error(request, _("Answer all %(total)s questions before submitting.") % {"total": len(questions)})
            else:
                awarded = submission.submit()
                if awarded:
                    messages.success(request, _("Submitted! You earned %(points)s points.") % {"points": submission.points_awarded})
                return redirect("learning:homework_detail", homework_id=homework.pk)
        else:
            messages.success(request, _("Progress saved. You can safely come back later."))
            return redirect("learning:homework_detail", homework_id=homework.pk)

    answers = {answer.question_id: answer for answer in submission.answers.all()}
    question_rows = [{"question": q, "answer": answers.get(q.pk)} for q in questions]
    answered_count = len(answers)
    progress = round((answered_count / len(questions)) * 100) if questions else 0
    return render(
        request,
        "learning/homework_detail.html",
        {
            "active_nav": "learn" if homework.is_course_checkpoint else "tasks",
            "homework": homework,
            "submission": submission,
            "question_rows": question_rows,
            "answered_count": answered_count,
            "total_questions": len(questions),
            "progress": progress,
            "course_navigation": _course_navigation(
                homework.section.course,
                student,
                active_section_id=homework.section_id,
                active_homework_id=homework.pk,
            ) if homework.section_id else None,
        },
    )


@login_required
@require_POST
def autosave_answer(request, homework_id):
    student = _student(request)
    homework = get_object_or_404(Homework, pk=homework_id)
    submission, created = Submission.objects.get_or_create(student=student, homework=homework)
    if submission.submitted_at:
        return JsonResponse({"ok": False, "error": _("This homework is already submitted.")}, status=409)
    try:
        payload = json.loads(request.body)
        question = homework.questions.get(pk=payload.get("question_id"))
        selected = payload.get("selected_option")
        if selected not in dict(Question.OPTION_CHOICES):
            raise ValueError
    except (ValueError, TypeError, json.JSONDecodeError, Question.DoesNotExist):
        return JsonResponse({"ok": False, "error": _("Invalid answer.")}, status=400)
    answer, created = Answer.objects.update_or_create(
        submission=submission, question=question, defaults={"selected_option": selected}
    )
    return JsonResponse(
        {
            "ok": True,
            "saved_at": timezone.localtime(answer.saved_at).strftime("%H:%M"),
            "answered": submission.answers.count(),
            "total": homework.questions.count(),
        }
    )


@login_required
def leaderboard(request):
    student = _student(request)
    students = list(Student.objects.all())
    return render(
        request,
        "learning/leaderboard.html",
        {"active_nav": "rank", "students": students, "current_student": student},
    )


@login_required
def profile(request):
    student = _student(request)
    courses = list(Course.objects.prefetch_related("sections__lessons").all())
    recent_submissions = student.submissions.select_related(
        "homework__section__course", "homework__lesson"
    ).filter(submitted_at__isnull=False).order_by("-submitted_at")[:5]
    completed_tasks = student.submissions.filter(submitted_at__isnull=False).count()
    return render(
        request,
        "learning/profile.html",
        {
            "active_nav": None,
            "student": student,
            "courses": courses,
            "recent_submissions": recent_submissions,
            "completed_tasks": completed_tasks,
        },
    )


@login_required
def attendance(request):
    student = _student(request)
    today = timezone.localdate()
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
        focus_date = date.fromisoformat(request.GET.get("date", today.isoformat()))
        if not 1 <= month <= 12:
            raise ValueError
    except (ValueError, TypeError):
        year, month, focus_date = today.year, today.month, today

    month_start = date(year, month, 1)
    month_end = date(year, month, calendar.monthrange(year, month)[1])
    session_query = AttendanceSession.objects.select_related("lesson__section").filter(
        date__range=(month_start, month_end)
    )
    sessions = {item.date: item for item in session_query}
    task_query = Homework.objects.select_related("lesson", "section__course").filter(
        Q(kind=Homework.INDEPENDENT)
        | Q(kind=Homework.COURSE, section__course__enrollments__student=student),
        deadline__date__range=(month_start, month_end),
    ).distinct()
    tasks = []
    tasks_by_date = {}
    course_tasks_by_date = {}
    independent_tasks_by_date = {}
    for homework in task_query:
        task = {
            "homework": homework,
            "status": homework.status_for(student),
        }
        due_date = timezone.localdate(homework.deadline)
        tasks.append(task)
        tasks_by_date.setdefault(due_date, []).append(task)
        target = (
            course_tasks_by_date
            if homework.kind == Homework.COURSE
            else independent_tasks_by_date
        )
        target.setdefault(due_date, []).append(task)
    cal = calendar.Calendar(firstweekday=0)
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        weeks.append(
            [
                {
                    "date": day,
                    "day": day.day,
                    "in_month": day.month == month,
                    "is_today": day == today,
                    "session": sessions.get(day),
                    "tasks": tasks_by_date.get(day, []),
                    "course_tasks": course_tasks_by_date.get(day, []),
                    "independent_tasks": independent_tasks_by_date.get(day, []),
                }
                for day in week
            ]
        )
    selected_session = sessions.get(focus_date)
    selected_course_tasks = course_tasks_by_date.get(focus_date, [])
    selected_independent_tasks = independent_tasks_by_date.get(focus_date, [])
    status_counts = AttendanceSession.objects.filter(date__range=(month_start, month_end)).aggregate(
        attended=Count("id", filter=Q(status="attended")),
        missed=Count("id", filter=Q(status="missed")),
        scheduled=Count("id", filter=Q(status="scheduled")),
    )
    task_counts = {
        "total": len(tasks),
        "independent": sum(item["homework"].kind == Homework.INDEPENDENT for item in tasks),
        "course": sum(item["homework"].kind == Homework.COURSE for item in tasks),
    }
    previous = month_start - timedelta(days=1)
    next_month = month_end + timedelta(days=1)
    return render(
        request,
        "learning/attendance.html",
        {
            "active_nav": "attendance",
            "weeks": weeks,
            "month_label": month_start,
            "year": year,
            "month": month,
            "previous": previous,
            "next_month": next_month,
            "focus_date": focus_date,
            "selected_session": selected_session,
            "selected_course_tasks": selected_course_tasks,
            "selected_independent_tasks": selected_independent_tasks,
            "status_counts": status_counts,
            "task_counts": task_counts,
            "weekday_labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        },
    )
