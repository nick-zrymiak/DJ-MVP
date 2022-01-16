from django.db import models
from django.conf import settings

def upload_to(instance, filename):
    return 'posts/{filename}'.format(filename=filename)

class Video(models.Model):
    # default
    # unique
    # null
    audio = models.FileField(upload_to=upload_to, default='default_media/default_audio.mp3')
    motion_direction = models.IntegerField(default=90)
    motion_intensity = models.IntegerField(default=50)
    hue = models.IntegerField(default=50)
    saturation = models.IntegerField(default=50)
    brightness = models.IntegerField(default=50)
    contrast = models.IntegerField(default=50)
    red = models.IntegerField(default=50)
    green = models.IntegerField(default=50)
    blue = models.IntegerField(default=50)
    video_shift = models.IntegerField(default=0)
    repeated_segments = models.IntegerField(default=4)
    repeated_songs = models.IntegerField(default=5)
    
    black_and_white = models.BooleanField(default=False)
    fade = models.TextField(default='None')
    mirror = models.TextField(default='None')
    rotate = models.BooleanField(default=False)
    scroll = models.BooleanField(default=False)
    datamosh = models.BooleanField(default=False)
    reverse = models.BooleanField(default=False)
    paintify = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    