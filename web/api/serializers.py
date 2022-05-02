from rest_framework import serializers
from .models import Video

class CreateVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('audio',
                  'motion_direction_min',
                  'motion_direction_max', 
                  'motion_intensity_min',
                  'motion_intensity_max',
                  'audio_video_alignment',
                  'max_repeated_segments',
                  'max_repeated_songs',
                  'red_average',
                  'red_std',
                  'green_average',
                  'green_std',
                  'blue_average',
                  'blue_std',
                  'black_and_white',
                  'fade',
                  'mirror',
                  'datamosh',
                  'paintify')
        