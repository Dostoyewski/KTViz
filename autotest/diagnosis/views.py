from django.shortcuts import render

from .models import TestingRecording


def main_view(request):
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
                      "dists": f(rec.dists.split(sep='::'))})
    return render(request, 'main.html', context={'data': s_rec})
