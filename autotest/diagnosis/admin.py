from django.contrib import admin

from .models import TestingRecording, Scenario, ScenariosSet


class TestingRecordingAdmin(admin.ModelAdmin):
    list_display = ('date', 'file')


class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('name', 'num_targets', 'dist1', 'dist2')


class ScenariosSetAdmin(admin.ModelAdmin):
    list_display = ('n_targets', 'n_cases', 'metafile')


admin.site.register(TestingRecording, TestingRecordingAdmin)
admin.site.register(Scenario, ScenarioAdmin)
admin.site.register(ScenariosSet, ScenariosSetAdmin)
