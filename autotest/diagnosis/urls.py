from django.urls import path

from . import views

urlpatterns = [
    path('', views.main_view, name='main'),
    path('upload/', views.upload_file, name='upload'),
]
