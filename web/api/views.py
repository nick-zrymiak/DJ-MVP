from django.shortcuts import render
from rest_framework import generics, status
from .serializers import VideoSerializer, CreateVideoSerializer
from .models import Video
from rest_framework.views import APIView
from rest_framework.response import Response

class VideoView(generics.CreateAPIView):
    query_set = Video.objects.all()
    serializer_class = VideoSerializer

class CreateVideoView(APIView):
    serializer_class = CreateVideoSerializer
    
    def post(self, request, format=None):
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()
            
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            motion_direction = serializer.data.get('motion_direction')
            motion_intensity = serializer.data.get('motion_intensity')
            hue = serializer.data.get('hue')
            saturation = serializer.data.get('saturation')
            brightness = serializer.data.get('brightness')
            contrast = serializer.data.get('contrast')
            red = serializer.data.get('red')
            green = serializer.data.get('green')
            blue = serializer.data.get('blue')
            video_shift = serializer.data.get('video_shift')
            repeated_segments = serializer.data.get('repeated_segments')
            repeated_songs = serializer.data.get('repeated_songs')
            
            black_and_white = serializer.data.get('black_and_white')
            fade = serializer.data.get('fade')
            mirror = serializer.data.get('mirror')
            rotate = serializer.data.get('rotate')
            scroll = serializer.data.get('scroll')
            datamosh = serializer.data.get('datamosh')
            reverse = serializer.data.get('reverse')
            paintify = serializer.data.get('paintify')        
            
            video = Video(motion_direction=motion_direction, 
                          motion_intensity=motion_intensity,
                          hue=hue,
                          saturation=saturation,
                          brightness=brightness,
                          contrast=contrast,
                          red=red,
                          green=green,
                          blue=blue,
                          video_shift=video_shift,
                          repeated_segments=repeated_segments,
                          repeated_songs=repeated_songs,
                          black_and_white=black_and_white,
                          fade=fade,
                          mirror=mirror,
                          rotate=rotate,
                          scroll=scroll,
                          datamosh=datamosh,
                          reverse=reverse,
                          paintify=paintify)
            video.save()
            return Response(CreateVideoSerializer(video).data, status=status.HTTP_201_CREATED)
        
        return Response({'Bad Request': 'Invalid data...'}, status=status.HTTP_400_BAD_REQUEST)
    