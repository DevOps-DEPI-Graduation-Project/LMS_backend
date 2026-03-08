from django.contrib import admin
from videos.models import Video, VideoProgress

# Register your models here.
admin.site.register(Video)
admin.site.register(VideoProgress)