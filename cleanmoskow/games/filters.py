from django.contrib.admin import SimpleListFilter
from django.db import models

class CorrectPercentageFilter(SimpleListFilter):
    title = 'Процент правильных'
    parameter_name = 'correct_percentage_range'

    def lookups(self, request, model_admin):
        return [
            ('0', '0%'),
            ('1-49', '1%–49%'),
            ('50-74', '50%–74%'),
            ('75-100', '75%–100%'),
        ]

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.filter(total_answers=0)
        elif self.value() == '1-49':
            return queryset.filter(total_answers__gt=0).filter(
                correct_answers__lt=models.F('total_answers') * 0.5)
        elif self.value() == '50-74':
            return queryset.filter(
                correct_answers__gte=models.F('total_answers') * 0.5,
                correct_answers__lt=models.F('total_answers') * 0.75
            )
        elif self.value() == '75-100':
            return queryset.filter(
                correct_answers__gte=models.F('total_answers') * 0.75
            )
        return queryset
