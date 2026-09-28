import calendar
import json
from datetime import date, timedelta

from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .models import Answer, AttendanceSession, DemoConfig, Homework, Lesson, Question, Student, Submission


def _student():
    return get_object_or_404(Student, is_demo=True)


def _homework_cards(student):
    cards = []
    for homework in Homework.objects.select_related("lesson").prefetch_related("submissions__answers"):
        submission = homework.submission_for(student)
        cards.append(
            {
                "homework": homework,
                "submission": submission,
                "status": homework.status_for(student),
                "answered": submission.answers.count() if submission else 0,
                "total": homework.questions.count(),
            }
        )
    return cards


def dashboard(request):
    student = _student()
    today_lesson = Lesson.objects.filter(is_today=True).first() or Lesson.objects.first()
    cards = _homework_cards(student)
    pending = [card for card in cards if card["status"] != "completed"]
    priority = next((card for card in pending if card["status"] == "in_progress"), pending[0] if pending else None)
    config = DemoConfig.objects.first()
    countdown = max((config.exam_date - timezone.localdate()).days, 0) if config else 0
    lessons = Lesson.objects.all()
    learning_progress = round(sum(item.progress_percent for item in lessons) / lessons.count()) if lessons else 0
    return render(
        request,
        "learning/dashboard.html",
        {
            "active_nav": "home",
            "today_lesson": today_lesson,
            "pending_count": len(pending),
            "priority": priority,
            "countdown": countdown,
            "exam_date": config.exam_date if config else None,
            "learning_progress": learning_progress,
            "rank": student.rank,
            "student_count": Student.objects.count(),
        },
    )


def learn(request):
    lesson = Lesson.objects.filter(is_today=True).first() or Lesson.objects.first()
    if not lesson:
        return render(request, "learning/empty.html", {"active_nav": "learn"})
    return lesson_detail(request, lesson.pk)


def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related("homework"), pk=lesson_id)
    other_lessons = Lesson.objects.exclude(pk=lesson.pk)[:3]
    return render(
        request,
        "learning/lesson_detail.html",
        {"active_nav": "learn", "lesson": lesson, "other_lessons": other_lessons},
    )


def homework_list(request):
    student = _student()
    cards = _homework_cards(student)
    counts = {key: sum(card["status"] == key for card in cards) for key in ("not_started", "in_progress", "overdue", "completed")}
    return render(
        request,
        "learning/homework_list.html",
        {"active_nav": "tasks", "cards": cards, "counts": counts},
    )


def homework_detail(request, homework_id):
    student = _student()
    homework = get_object_or_404(Homework.objects.select_related("lesson"), pk=homework_id)
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
            "active_nav": "tasks",
            "homework": homework,
            "submission": submission,
            "question_rows": question_rows,
            "answered_count": answered_count,
            "total_questions": len(questions),
            "progress": progress,
        },
    )


@require_POST
def autosave_answer(request, homework_id):
    student = _student()
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


def leaderboard(request):
    student = _student()
    students = list(Student.objects.all())
    return render(
        request,
        "learning/leaderboard.html",
        {"active_nav": "rank", "students": students, "current_student": student},
    )


def attendance(request):
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
    sessions = {item.date: item for item in AttendanceSession.objects.filter(date__range=(month_start, month_end))}
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
                }
                for day in week
            ]
        )
    selected = sessions.get(focus_date) or next(iter(sessions.values()), None)
    status_counts = AttendanceSession.objects.filter(date__range=(month_start, month_end)).aggregate(
        attended=Count("id", filter=Q(status="attended")),
        missed=Count("id", filter=Q(status="missed")),
        scheduled=Count("id", filter=Q(status="scheduled")),
    )
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
            "selected": selected,
            "status_counts": status_counts,
            "weekday_labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        },
    )
