from django.contrib import admin

from .models import Answer, AttendanceSession, DemoConfig, Homework, Lesson, Question, Student, Submission

admin.site.register([DemoConfig, Student, Lesson, Homework, Question, Submission, Answer, AttendanceSession])
