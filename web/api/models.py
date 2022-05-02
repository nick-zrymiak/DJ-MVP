from django.db import models
from django.conf import settings

def upload_to(instance, filename):
    return 'posts/{filename}'.format(filename=filename)

class Video(models.Model):
    # default
    # unique
    # null
    audio = models.FileField(upload_to=upload_to, default='default_media/default_audio.mp3')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # segment selection parameters
    motion_direction_min = models.IntegerField(default=0)
    motion_direction_max = models.IntegerField(default=360)
    motion_intensity_min = models.IntegerField(default=0)
    motion_intensity_max = models.IntegerField(default=100)
    audio_video_alignment = models.IntegerField(default=0)
    max_repeated_segments = models.IntegerField(default=10)
    max_repeated_songs = models.IntegerField(default=10)
    red_average = models.FloatField(default=128)
    red_std = models.FloatField(default=3)
    green_average = models.FloatField(default=128)
    green_std = models.FloatField(default=3)
    blue_average = models.FloatField(default=128)
    blue_std = models.FloatField(default=3)
    
    # visual effects parameters
    black_and_white = models.BooleanField(default=False)
    fade = models.TextField(default='None')
    mirror = models.TextField(default='None')
    datamosh = models.BooleanField(default=False)
    paintify = models.BooleanField(default=False)
