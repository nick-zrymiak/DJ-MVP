from django.shortcuts import render
from rest_framework import generics, status
from .serializers import CreateVideoSerializer
from .models import Video
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import HttpResponse
from django.core.files import File
import os.path
from web.settings import BASE_DIR, MEDIA_ROOT
import time
from music_video_generation.video_generation import *
from music_video_generation.audio_similarity import *
from music_video_generation.segment_videos import *

def is_being_written_to(filepath):
        os.umask(0)
        with open(os.open(filepath, os.O_CREAT | os.O_WRONLY, 0o777), 'w') as fh:
            return False
         
        return True
 
@api_view(['GET'])
def DownloadFile(self):
    posted_videos = txt_to_list('./posted_videos.txt')
    path_to_file = posted_videos[-1]
    f = open(path_to_file, 'rb')
    file = File(f)
    response = HttpResponse(file.read())
    response['Content-Disposition'] = 'attachment';
    
    return response
 
class CreateVideoView(APIView):
    serializer_class = CreateVideoSerializer
 
    def post(self, request, format=None):
        serializer = CreateVideoSerializer(data=request.data)
        print(request.data)
          
        if serializer.is_valid():
            serializer.save()
 
            filepath = str(BASE_DIR) + serializer.data['audio']
            while is_being_written_to(filepath):
                time.sleep(1)
                 
            generate_music_video(filepath)
            video_path = get_video_path(filepath)
            append_to_txt('./posted_videos.txt', video_path)
        
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
