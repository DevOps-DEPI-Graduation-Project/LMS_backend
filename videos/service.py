import threading
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.core.exceptions import ValidationError
from videos.models import Video
from videos.tasks import process_video_pipeline
from cources.models import Course

class VideoService:
    @staticmethod
    def create_or_update_video(video_slug=None, **video_data):
        with transaction.atomic():
            if video_slug:
                try:
                    video = Video.objects.select_for_update().get(slug=video_slug)
                except Video.DoesNotExist:
                    raise Http404("Video not found.")
                
                snapshot_upload = video.video_upload.name if video.video_upload else None
                snapshot_url = video.video_url
                
                for field, value in video_data.items():
                    setattr(video, field, value)
                    
                current_file = video.video_upload.name if video.video_upload else None
                trigger_pipeline = False
                
                if str(current_file) != str(snapshot_upload) or video.video_url != snapshot_url:
                    video.duration = None
                    video.status = 'processing'
                    trigger_pipeline = True
                    video.save()
                else:
                    video.save()
            else:
                video = Video(**video_data)
                
                try:
                    parent_course = Course.objects.select_for_update().get(pk=video.course_id)
                except Course.DoesNotExist:
                    raise ValidationError("Parent course does not exist.")
                    
                max_order = Video.objects.filter(course=parent_course).aggregate(Max('order'))['order__max'] or 0
                video.order = max_order + 1
                
                video.status = 'processing'
                video.save()
                trigger_pipeline = True

            if trigger_pipeline:
                transaction.on_commit(
                    lambda: threading.Thread(
                        target=process_video_pipeline,
                        args=(video.id,),
                        daemon=True
                    ).start()
                )
                
        return video