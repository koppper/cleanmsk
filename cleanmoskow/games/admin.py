from django.contrib import admin
import json 
from .models import GameSession, Leaderboard, QuizQuestions, CensoredWord
from django.utils.safestring import mark_safe
from django import forms


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "username", "score")
    search_fields = ("user",)
import ast


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

        # Если уже список — просто вернуть его
        if isinstance(raw_data, list):
            return raw_data

        try:
            # Попробовать распарсить как JSON-строку или питоновский список
            parsed = ast.literal_eval(raw_data)
            if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
                return parsed
        except (ValueError, SyntaxError):
            pass

        # Иначе — обычная обработка строки
        lines = raw_data.strip().split("\n")
        return [line.strip() for line in lines if line.strip()]

@admin.register(QuizQuestions)
class QuizQuestionsAdmin(admin.ModelAdmin):
    form = QuizQuestionsAdminForm
    list_display = ("id", "question", "correct_answer", "explanation", "tip_link", "correct_percentage")
    search_fields = ("question",)
    def correct_percentage(self, obj):
        return obj.correct_percentage()
    correct_percentage.short_description = "Процент правильных ответов"

@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "formatted_question", "current_question_index", "finished", "created_at")
    search_fields = ("user__uuid", "user__username", "user__user__username")
    readonly_fields = ("display_questions",)
    exclude = ("questions",)
    list_filter = ("finished", "user",)

    change_list_template = "admin/api/gamesession/change_list.html"

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}

        total_games = GameSession.objects.count()
        started_users = GameSession.objects.exclude(user=None).values('user').count()
        finished_count = GameSession.objects.filter(finished=True).values('user').count()

        completion_rate = round((finished_count / started_users * 100), 2) if started_users else 0

        extra_context.update({
            'total_games': total_games,
            'started_users': started_users,
            'completion_rate': completion_rate,
        })

        return super().changelist_view(request, extra_context=extra_context)


    @admin.display(description="Вопросы")
    def formatted_question(self, obj):
        """Форматирование списка вопросов для удобного отображения"""
        questions = json.loads(obj.questions) if isinstance(obj.questions, str) else obj.questions
        if not questions:
            return "Нет вопросов"
        return mark_safe("<br>".join([f"{i+1}. {q['question']}" for i, q in enumerate(questions)]))
    
    def display_questions(self, obj):
        """Форматированное отображение вопросов внутри GameSession"""
        try:
            questions = json.loads(obj.questions) if isinstance(obj.questions, str) else obj.questions
        except (json.JSONDecodeError, TypeError):
            return "Ошибка в формате данных"

        if not questions:
            return "Нет вопросов"

        html = "<ul>"
        for q in questions:
            html += f"<li><strong>{q.get('question', 'Нет текста')}</strong><br>"
            html += f"Ответы: {', '.join(q.get('answers', []))}<br>"
            html += f"Правильный ответ: <b>{q.get('answers')[q.get('correct_answer', 0)]}</b><br>"
            html += f"<a href='{q.get('tip_link', '#')}' target='_blank'>Подробнее</a></li><br>"
        html += "</ul>"

        return mark_safe(html)

    display_questions.short_description = "Список вопросов"


@admin.register(CensoredWord)
class CensoredWordAdmin(admin.ModelAdmin):
    list_display = ("word",)
    search_fields = ("word",)
