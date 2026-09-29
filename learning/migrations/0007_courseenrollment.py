import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("learning", "0006_course_cover_image_course_instructor_name_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="CourseEnrollment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("enrolled_at", models.DateTimeField(auto_now_add=True)),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="learning.course",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="course_enrollments",
                        to="learning.student",
                    ),
                ),
            ],
            options={
                "ordering": ["enrolled_at", "id"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("student", "course"),
                        name="unique_student_course_enrollment",
                    )
                ],
            },
        ),
    ]
