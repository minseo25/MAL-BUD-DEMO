from django.urls import path
from . import views

urlpatterns = [
    path('vlm/', views.voice_api, name='voice_api'),
]
