from django.contrib import admin

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

admin.site.register(
    [
        Course,
        CourseEnrollment,
        CourseSection,
        DemoConfig,
        Student,
        Lesson,
        Homework,
        Question,
        Submission,
        Answer,
        AttendanceSession,
    ]
)
