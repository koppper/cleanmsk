from django.contrib import admin, messages
import json 
from .models import GameSession, Leaderboard, QuizQuestions, CensoredWord
from django.utils.safestring import mark_safe
from django import forms
from django.urls import path
from django.shortcuts import redirect, render
from .forms import CensoredWordImportForm, QuizQuestionsAdminForm
import csv
import io
from .filters import CorrectPercentageFilter

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "score")
    search_fields = ("user__username",)


@admin.register(QuizQuestions)
class QuizQuestionsAdmin(admin.ModelAdmin):
    form = QuizQuestionsAdminForm
    list_display = ("id", "question", "correct_answer", "explanation", "tip_link", "correct_percentage")
    search_fields = ("question",)
    list_filter = ("correct_answer", CorrectPercentageFilter)

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

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("import/", self.admin_site.admin_view(self.import_view), name="censoredword_import"),
        ]
        return custom_urls + urls

    def import_view(self, request):
        if request.method == "POST":
            form = CensoredWordImportForm(request.POST, request.FILES)
            if form.is_valid():
                file = form.cleaned_data["file"]
                ext = file.name.split(".")[-1].lower()
                count = 0

                if ext == "txt":
                    content = file.read().decode("utf-8")
                    words = content.strip().splitlines()
                    for word in words:
                        if word.strip():
                            CensoredWord.objects.get_or_create(word=word.strip())
                            count += 1

                elif ext == "csv":
                    content = file.read().decode("utf-8")
                    reader = csv.DictReader(io.StringIO(content))
                    for row in reader:
                        word = row.get("word")
                        if word:
                            CensoredWord.objects.get_or_create(word=word.strip())
                            count += 1
                else:
                    messages.error(request, "Поддерживаются только .txt и .csv файлы")
                    return redirect("..")

                messages.success(request, f"Импортировано {count} слов!")
                return redirect("..")
        else:
            form = CensoredWordImportForm()

        context = {
            "form": form,
            "title": "Импорт цензурных слов",
        }
        return render(request, "admin/games/censoredword/import_form.html", context)
