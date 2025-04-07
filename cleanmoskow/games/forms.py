from django import forms
import ast
from .models import QuizQuestions
class CensoredWordImportForm(forms.Form):
    file = forms.FileField(
        label="Файл со словами",
        help_text="Загрузите .txt (по одному слову в строке) или .csv (с колонкой 'word')"
    )


class QuizQuestionsAdminForm(forms.ModelForm):
    answers = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4, "cols": 40}),
        help_text="Введите каждый вариант ответа с новой строки."
    )

    class Meta:
        model = QuizQuestions
        fields = "__all__"

    def clean_answers(self):
        raw_data = self.cleaned_data["answers"]

        if isinstance(raw_data, list):
            return raw_data

        try:
            parsed = ast.literal_eval(raw_data)
            if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
                return parsed
        except (ValueError, SyntaxError):
            pass

        lines = raw_data.strip().split("\n")
        return [line.strip() for line in lines if line.strip()]

