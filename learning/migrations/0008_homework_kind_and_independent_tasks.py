import django.db.models.deletion
from django.db import migrations, models


def classify_existing_homework(apps, schema_editor):
    Homework = apps.get_model("learning", "Homework")
    for homework in Homework.objects.select_related("lesson"):
        homework.kind = "course"
        if homework.lesson_id:
            homework.subject = homework.lesson.subject
        homework.save(update_fields=["kind", "subject"])


class Migration(migrations.Migration):

    dependencies = [
        ("learning", "0007_courseenrollment"),
    ]

    operations = [
        migrations.AddField(
            model_name="homework",
            name="assigned_by",
            field=models.CharField(default="Cereqo academic team", max_length=100),
        ),
        migrations.AddField(
            model_name="homework",
            name="kind",
            field=models.CharField(
                choices=[("course", "Course checkpoint"), ("independent", "Independent task")],
                db_index=True,
                default="course",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="homework",
            name="subject",
            field=models.CharField(
                choices=[("math", "Math"), ("rw", "Reading & Writing")],
                default="math",
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="homework",
            name="lesson",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="homework",
                to="learning.lesson",
            ),
        ),
        migrations.RunPython(classify_existing_homework, migrations.RunPython.noop),
    ]
