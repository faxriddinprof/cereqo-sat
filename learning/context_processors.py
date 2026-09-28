from .models import Student


def demo_shell(request):
    student = Student.objects.filter(is_demo=True).first()
    return {"demo_student": student}
