import datetime

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .forms import UploadFileForm
from .models import TestingRecording


def main_view(request):
    """
    Plots graphs from info aus DB
    @param request:
    @return:
    """
    recordings = TestingRecording.objects.all()
    s_rec = []
    f = lambda arr: [float(a) for a in arr]
    for rec in recordings:
        s_rec.append({"date": str(rec.date),
                      "code0": f(rec.code0.split(sep='::')),
                      "code1": f(rec.code1.split(sep='::')),
                      "code2": f(rec.code2.split(sep='::')),
                      "code4": f(rec.code4.split(sep='::')),
                      "code5": f(rec.code5.split(sep='::')),
                      "dists": f(rec.dists.split(sep='::')),
                      "n_targ": rec.n_targets,
                      "title": rec.title})
    return render(request, 'main.html', context={'data': s_rec})


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            obj = TestingRecording()
            obj.date = datetime.datetime.now()
            obj.file = form.cleaned_data['file']
            obj.title = form.cleaned_data['title']
            obj.save()
            return HttpResponseRedirect(reverse('main'))
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})


def handle_uploaded_file(f):
    with open('some/file/name.txt', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
