from django.contrib import admin

from .models import TestingRecording


class TestingRecordingAdmin(admin.ModelAdmin):
    list_display = ('date', 'file')


admin.site.register(TestingRecording, TestingRecordingAdmin)
