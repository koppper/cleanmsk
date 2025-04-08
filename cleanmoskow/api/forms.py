from django import forms

class ImageZipUploadForm(forms.Form):
    zip_file = forms.FileField(label="Загрузите ZIP архив с картинками")