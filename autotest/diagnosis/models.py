import datetime

from django.db import models


class TestingRecording(models.Model):
    date = models.DateTimeField(default=datetime.datetime.now)
    file = models.FileField(upload_to='')
    # We will storage all plots data in string format using '::' delimiter
    code0 = models.TextField(blank=True, default='', max_length=2000)
    code1 = models.TextField(blank=True, default='', max_length=2000)
    code2 = models.TextField(blank=True, default='', max_length=2000)
    code4 = models.TextField(blank=True, default='', max_length=2000)
    code5 = models.TextField(blank=True, default='', max_length=2000)
    dists = models.TextField(blank=True, default='', max_length=2000)
