from rest_framework import serializers
from .models import Video

class CreateVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('audio',
                  'motion_direction', 
                  'motion_intensity',
                  'hue',
                  'saturation',
                  'brightness',
                  'contrast',
                  'red',
                  'green',
                  'blue',
                  'video_shift',
                  'repeated_segments',
                  'repeated_songs',
                  'black_and_white',
                  'fade',
                  'mirror',
                  'rotate',
                  'scroll',
                  'datamosh',
                  'reverse',
                  'paintify')
        