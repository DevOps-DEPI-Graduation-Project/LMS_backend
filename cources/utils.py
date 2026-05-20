from videos.models import VideoProgress
def calculate_course_progress(user, course):
    student = getattr(user,"student_profile",None)
    if not student:
        return 0
    
    from users.models import Student
    
    if not isinstance(student, Student):
        raise TypeError("calculate_course_progress expects a Student instance")
    
    total_videos = course.videos.count()
    
    if total_videos == 0:
        return 0

    completed_videos = VideoProgress.objects.filter(
        student=student,
        video__course=course,
        is_completed=True 
    ).count()
    
    progress_percentage = int((completed_videos / total_videos) * 100)
    
    return min(progress_percentage, 100)

def get_course_status(progress):
    if progress == 0:
        return "not_started"
    elif progress < 100:
        return "in_progress"
    return "completed"
