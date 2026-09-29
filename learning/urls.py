from django.urls import path

from . import views

app_name = "learning"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("learn/", views.learn, name="learn"),
    path("courses/<int:course_id>/", views.course_detail, name="course_detail"),
    path("learn/sections/<int:section_id>/", views.section_detail, name="section_detail"),
    path("lessons/<int:lesson_id>/", views.lesson_detail, name="lesson_detail"),
    path("tasks/", views.homework_list, name="homework_list"),
    path("tasks/<int:homework_id>/", views.homework_detail, name="homework_detail"),
    path("tasks/<int:homework_id>/autosave/", views.autosave_answer, name="autosave_answer"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
    path("attendance/", views.attendance, name="attendance"),
    path("profile/", views.profile, name="profile"),
]
