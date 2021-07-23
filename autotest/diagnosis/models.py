import datetime
import os

from django.db import models

from .build_graphs import build_percent_diag


class TestingRecording(models.Model):
    date = models.DateTimeField(default=datetime.datetime.now)
    file = models.FileField(upload_to='')
    title = models.TextField(default="", max_length=1000)
    # We will storage all plots data in string format using '::' delimiter
    code0 = models.TextField(blank=True, default='', max_length=2000)
    code1 = models.TextField(blank=True, default='', max_length=2000)
    code2 = models.TextField(blank=True, default='', max_length=2000)
    code4 = models.TextField(blank=True, default='', max_length=2000)
    code5 = models.TextField(blank=True, default='', max_length=2000)
    n_targets = models.IntegerField(default=1)
    dists = models.TextField(blank=True, default='', max_length=2000)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        filename = os.path.split(self.file.path)
        filename = os.path.splitext(filename[1])[0]
        self.date = datetime.datetime.strptime(filename.split(sep='_')[1], "%Y-%m-%d").date()
        codes = build_percent_diag(self.file.path, 12, 4, 0.5, False)
        self.code0 = process_array(codes[0])
        self.code1 = process_array(codes[1])
        self.code2 = process_array(codes[2])
        self.code4 = process_array(codes[3])
        self.code5 = process_array(codes[4])
        self.dists = process_array(codes[5])
        self.n_targets = codes[6]
        super().save(*args, **kwargs)


def process_array(arr):
    s = ""
    for i, a in enumerate(arr):
        s += str(a)
        if i != len(arr) - 1:
            s += "::"
    return s
