from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.utils import timezone


class DemoConfig(models.Model):
    name = models.CharField(max_length=60, unique=True, default="Cereqo demo")
    exam_date = models.DateField()

    def __str__(self):
        return self.name


class Student(models.Model):
    name = models.CharField(max_length=100, unique=True)
    initials = models.CharField(max_length=3)
    points = models.PositiveIntegerField(default=0)
    streak = models.PositiveIntegerField(default=0)
    badge = models.CharField(max_length=80, blank=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        ordering = ["-points", "name"]

    def __str__(self):
        return self.name

    @property
    def rank(self):
        return Student.objects.filter(points__gt=self.points).count() + 1


class Course(models.Model):
    title = models.CharField(max_length=160)
    code = models.SlugField(max_length=60, unique=True)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    target_score = models.PositiveSmallIntegerField(default=1400)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-is_active", "start_date", "id"]

    def __str__(self):
        return self.title

    @property
    def progress_percent(self):
        lessons = Lesson.objects.filter(section__course=self)
        total = lessons.count()
        return round(sum(lessons.values_list("progress_percent", flat=True)) / total) if total else 0


class CourseSection(models.Model):
    SUBJECT_CHOICES = [("math", "Math"), ("rw", "Reading & Writing")]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=160)
    domain = models.CharField(max_length=120)
    subject = models.CharField(max_length=10, choices=SUBJECT_CHOICES)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    order = models.PositiveSmallIntegerField(default=1)
    exam_weight_percent = models.PositiveSmallIntegerField(default=25)

    class Meta:
        ordering = ["course", "order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["course", "order"], name="unique_course_section_order")
        ]

    def __str__(self):
        return f"{self.course.title} · {self.order}. {self.title}"

    @property
    def progress_percent(self):
        lessons = self.lessons.all()
        total = lessons.count()
        return round(sum(lessons.values_list("progress_percent", flat=True)) / total) if total else 0

    def status_for(self, student):
        checkpoint = getattr(self, "checkpoint", None)
        if checkpoint and checkpoint.status_for(student) == "completed":
            return "completed"
        today = timezone.localdate()
        if self.start_date > today:
            return "upcoming"
        if self.end_date < today:
            return "needs_attention"
        return "current"


class Lesson(models.Model):
    SUBJECT_CHOICES = [("math", "Math"), ("rw", "Reading & Writing")]
    title = models.CharField(max_length=160)
    section = models.ForeignKey(
        CourseSection, on_delete=models.CASCADE, related_name="lessons", null=True, blank=True
    )
    subject = models.CharField(max_length=10, choices=SUBJECT_CHOICES)
    topic = models.CharField(max_length=120)
    duration_minutes = models.PositiveSmallIntegerField(default=8)
    session_minutes = models.PositiveSmallIntegerField(default=75)
    summary = models.TextField()
    material = models.TextField()
    video_file = models.CharField(max_length=255, default="cereqo/video/demo-lesson-video.mp4")
    progress_percent = models.PositiveSmallIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_today = models.BooleanField(default=False)
    scheduled_date = models.DateField(null=True, blank=True)
    sequence = models.PositiveSmallIntegerField(default=1)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class Homework(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name="homework")
    section = models.OneToOneField(
        CourseSection, on_delete=models.CASCADE, related_name="checkpoint", null=True, blank=True
    )
    title = models.CharField(max_length=160)
    description = models.TextField()
    deadline = models.DateTimeField()
    max_points = models.PositiveSmallIntegerField(default=100)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "deadline"]

    def __str__(self):
        return self.title

    def submission_for(self, student):
        return self.submissions.filter(student=student).first()

    def status_for(self, student):
        submission = self.submission_for(student)
        if submission and submission.submitted_at:
            return "completed"
        if submission and submission.answers.exists():
            return "in_progress"
        if self.deadline < timezone.now():
            return "overdue"
        return "not_started"


class Question(models.Model):
    OPTION_CHOICES = [(key, key) for key in "ABCD"]
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name="questions")
    position = models.PositiveSmallIntegerField()
    prompt = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    explanation = models.TextField()

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["homework", "position"], name="unique_question_position")
        ]

    def __str__(self):
        return f"{self.homework.title} · Q{self.position}"

    @property
    def options(self):
        return [("A", self.option_a), ("B", self.option_b), ("C", self.option_c), ("D", self.option_d)]


class Submission(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="submissions")
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name="submissions")
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveSmallIntegerField(null=True, blank=True)
    points_awarded = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "homework"], name="unique_student_homework")
        ]

    @property
    def is_late(self):
        return bool(self.submitted_at and self.submitted_at > self.homework.deadline)

    def submit(self):
        if self.submitted_at:
            return False
        with transaction.atomic():
            locked = Submission.objects.select_for_update().get(pk=self.pk)
            if locked.submitted_at:
                self.refresh_from_db()
                return False
            total = locked.homework.questions.count()
            correct = locked.answers.filter(selected_option=models.F("question__correct_option")).count()
            score = round((correct / total) * 100) if total else 0
            points = round((score / 100) * locked.homework.max_points)
            locked.score = score
            locked.points_awarded = points
            locked.submitted_at = timezone.now()
            locked.save(update_fields=["score", "points_awarded", "submitted_at", "updated_at"])
            Student.objects.filter(pk=locked.student_id).update(points=models.F("points") + points)
        self.refresh_from_db()
        return True


class Answer(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    selected_option = models.CharField(max_length=1, choices=Question.OPTION_CHOICES)
    saved_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["submission", "question"], name="unique_submission_answer")
        ]


class AttendanceSession(models.Model):
    STATUS_CHOICES = [
        ("attended", "Attended"),
        ("missed", "Missed"),
        ("scheduled", "Scheduled"),
    ]
    date = models.DateField(unique=True)
    lesson = models.OneToOneField(
        Lesson, on_delete=models.CASCADE, related_name="attendance_session", null=True, blank=True
    )
    title = models.CharField(max_length=140)
    subject = models.CharField(max_length=40)
    start_time = models.TimeField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.date}: {self.title}"
