from django.urls import path
from .views import GenerateQuestionsView

urlpatterns = [
    path('generate/<int:topic_id>/', GenerateQuestionsView.as_view(), name='generate-questions'),
]
