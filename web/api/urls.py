from django.urls import path
from .views import VideoView

urlpatterns = [
    path('video', VideoView.as_view()),
]