from django.urls import path
from .views import CreateVideoView, DownloadFile
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('video', CreateVideoView.as_view()),
    path('download', DownloadFile),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)