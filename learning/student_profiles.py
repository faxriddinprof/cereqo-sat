from .models import Student


def _unique_name(base_name, user):
    base_name = (base_name or "Cereqo learner").strip()[:90]
    candidate = base_name
    suffix = 2
    while Student.objects.filter(name=candidate).exclude(user=user).exists():
        candidate = f"{base_name[:86]} {suffix}"
        suffix += 1
    return candidate


def _initials(name):
    parts = [part for part in name.split() if part]
    if not parts:
        return "CL"
    return "".join(part[0] for part in parts[:2]).upper()


def student_for_user(user):
    if not user or not user.is_authenticated:
        return None

    try:
        return user.student_profile
    except Student.DoesNotExist:
        display_name = user.get_full_name() or user.email.split("@")[0] or user.get_username()
        display_name = _unique_name(display_name, user)
        return Student.objects.create(
            user=user,
            name=display_name,
            initials=_initials(display_name),
            badge="New learner",
        )
