from django import forms


class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()


class UploadMetaFileForm(forms.Form):
    n_targets = forms.IntegerField()
    metafile = forms.FileField()
