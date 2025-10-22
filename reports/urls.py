# report/urls.py
from django.urls import path
from .views import PerformanceSummaryView, QuizHistoryView

urlpatterns = [
    path('performance-summary/', PerformanceSummaryView.as_view(), name='performance-summary'),
    path('quiz-history/', QuizHistoryView.as_view(), name='quiz-history'),
]