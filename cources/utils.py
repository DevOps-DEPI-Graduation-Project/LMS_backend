from videos.models import VideoProgress
from quizzes.models import Attempt
from users.models import Student

def calculate_student_overall_progress(student, enrollments):

    total_items = 0
    completed_items = 0

    for enrollment in enrollments:
        course = enrollment.course

        # ===== Videos =====
        total_videos = course.videos.count()

        completed_videos = VideoProgress.objects.filter(
            student=student,
            video__course=course,
            is_completed=True
        ).count()

        # ===== Quizzes =====
        total_quizzes = course.quizzes.count()

        passed_quizzes = Attempt.objects.filter(
            student=student.user,
            quiz__course=course,
            status="passed"
        ).values("quiz").distinct().count()

        total_items += total_videos + total_quizzes
        completed_items += completed_videos + passed_quizzes

    if total_items == 0:
        return 0

    return round((completed_items / total_items) * 100, 2)

def calculate_course_progress(user, course):
    student = getattr(user, "student_profile", None)

    if not student:
        return 0

    if not isinstance(student, Student):
        raise TypeError("calculate_course_progress expects a Student instance")

    # ===== totals =====
    total_videos = course.videos.count()
    total_quizzes = course.quizzes.count()

    total_content = total_videos + total_quizzes

    if total_content == 0:
        return 0

    # ===== completed videos =====
    completed_videos = VideoProgress.objects.filter(
        student=student,
        video__course=course,
        is_completed=True
    ).count()

    # ===== passed quizzes =====
    passed_quizzes = Attempt.objects.filter(
        student=user,
        quiz__course=course,
        status="passed"
    ).values("quiz").distinct().count()

    # ===== final progress =====
    completed_content = completed_videos + passed_quizzes

    progress_percentage = int(
        (completed_content / total_content) * 100
    )

    return min(progress_percentage, 100)


def get_course_status(progress):
    if progress == 0:
        return "not_started"
    elif progress < 100:
        return "in_progress"
    return "completed"