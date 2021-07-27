from django.urls import path

from . import views

urlpatterns = [
    path('', views.main_view, name='main'),
    path('upload/', views.upload_file, name='upload'),
    path('upload/meta/', views.upload_metafile, name='upload_meta'),
]
