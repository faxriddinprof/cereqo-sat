from .student_profiles import student_for_user


def demo_shell(request):
    student = student_for_user(request.user)
    return {"demo_student": student}
