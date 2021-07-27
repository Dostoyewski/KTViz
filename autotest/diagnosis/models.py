import datetime
import os

import pandas as pd
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
        filename = os.path.splitext(os.path.split(self.file.path)[1])[0]
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


class ScenariosSet(models.Model):
    n_targets = models.IntegerField(default=1)
    n_cases = models.IntegerField(default=0)
    metafile = models.FileField(upload_to='', blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        df = pd.read_csv(self.metafile.path)
        self.n_cases = len(df['datadirs'])
        for name in df['datadirs']:
            obj = Scenario()
            obj.name = os.path.split(name)[1]
            obj.scenariosSet = self
            obj.save()
        super().save(*args, **kwargs)


class Scenario(models.Model):
    name = models.TextField(blank=True, default='', max_length=500)
    num_targets = models.IntegerField(default=1)
    dist1 = models.FloatField(default=0)
    dist2 = models.FloatField(default=0)
    vel1 = models.FloatField(default=0)
    vel2 = models.FloatField(default=0)
    vel_our = models.FloatField(default=0)
    course1 = models.FloatField(default=0)
    course2 = models.FloatField(default=0)
    scenariosSet = models.ForeignKey(ScenariosSet, on_delete=models.CASCADE, default=1)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
            names = self.name.split(sep='_')
            self.dist1 = names[1]
            self.dist2 = names[2]
            self.vel1 = names[3]
            self.vel2 = names[4]
            self.vel_our = names[5]
            self.course1 = names[6]
            self.course2 = names[7]
        except IndexError:
            pass
        super().save(*args, **kwargs)
