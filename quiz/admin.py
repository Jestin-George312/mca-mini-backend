from django.contrib import admin
from .models import QuizQuestion,QuizResult

# Register your models here.
admin.site.register(QuizQuestion)
admin.site.register(QuizResult)