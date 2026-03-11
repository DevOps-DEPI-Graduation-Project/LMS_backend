def calculate_course_progress(student, course):
    """
    TEMP logic
    later will be based on completed lessons/videos
    """
    return 0


def get_course_status(progress):
    if progress == 0:
        return "not_started"
    elif progress < 100:
        return "in_progress"
    return "completed"