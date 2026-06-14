import os
import tempfile
import uuid
import ffmpeg
import yt_dlp
import logging
from datetime import timedelta
from urllib.parse import urlparse
from celery import shared_task
from django.core.files import File
from django.apps import apps
from django.db import transaction

logger = logging.getLogger(__name__)

# FIX 6: Configured Celery production-grade auto-retry mechanics for self-healing processing pipelines
@shared_task(
    autoretry_for=(Exception,),
    max_retries=3,
    default_retry_delay=60,  # Wait 60 seconds before retrying failed tasks
    retry_backoff=True       # Exponential backoff (1m, 2m, 4m...)
)
def process_video_pipeline(video_id):
    Video = apps.get_model('videos', 'Video')
    
    try:
        with transaction.atomic():
            video = Video.objects.select_for_update().filter(id=video_id, status='processing').first()
            if not video:
                return
    except Video.DoesNotExist:
        return

    try:
        # CASE A: External URL Processing
        if video.video_url:
            hostname = urlparse(video.video_url).hostname or ""
            if "youtube" in hostname or "youtu.be" in hostname:
                ydl_opts = {'quiet': True, 'skip_download': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video.video_url, download=False)
                    ext_duration = info.get('duration')
                    if ext_duration:
                        calculated_duration = timedelta(seconds=int(ext_duration))
                        Video.objects.filter(id=video.id).update(
                            duration=calculated_duration,
                            status='ready'
                        )
            else:
                Video.objects.filter(id=video.id).update(status='ready')

        # CASE B: Local Upload Transcoding Processing
        elif video.video_upload:
            # FIX 2: Switched to secure tempfile utilities to prevent memory leaks and /tmp/ disk exhaustion
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_input:
                for chunk in video.video_upload.chunks():
                    temp_input.write(chunk)
                temp_input_path = temp_input.name

            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_output:
                temp_output_path = temp_output.name

            try:
                # Execute corporate FFmpeg compression standards
                (
                    ffmpeg
                    .input(temp_input_path)
                    .output(
                        temp_output_path,
                        vcodec='libx264',
                        acodec='aac',
                        pix_fmt='yuv420p',
                        **{'profile:v': 'main', 'level': '3.1'}
                    )
                    .overwrite_output()
                    .run(quiet=True)
                )

                probe = ffmpeg.probe(temp_output_path)
                duration_seconds = float(probe['format']['duration'])
                calculated_duration = timedelta(seconds=duration_seconds)

                new_filename = f"{video.slug}_h264.mp4"
                
                # FIX 1: Open the verified transient file context buffer. Django's Storage layer 
                # will automatically stream this directly to AWS S3 / Cloud Storage providers securely.
                with open(temp_output_path, 'rb') as f:
                    video.video_upload.save(new_filename, File(f), save=False)
                
                Video.objects.filter(id=video.id).update(
                    duration=calculated_duration,
                    status='ready',
                    video_upload=video.video_upload.name
                )

            finally:
                # Strict cleanup tracking to absolutely eliminate residual node disk overheads
                if os.path.exists(temp_input_path):
                    os.remove(temp_input_path)
                if os.path.exists(temp_output_path):
                    os.remove(temp_output_path)

    except Exception as e:
        logger.exception(f"Pipeline failed for video ID {video_id}. Retrying task... Error: {str(e)}")
        # If all retries are exhausted by Celery, update state to failed
        if process_video_pipeline.request.retries >= process_video_pipeline.max_retries:
            Video.objects.filter(id=video.id).update(status='failed')
        raise e  # re-raise to trigger Celery's built-in retry mechanics