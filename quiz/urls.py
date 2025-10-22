# quiz/urls.py

from django.urls import path
# ✅ Import the new view
from .views import GenerateQuestionsView, GetQuestionsByTopicView, SaveQuizResponseView

urlpatterns = [
    path('generate/<int:topic_id>/', GenerateQuestionsView.as_view(), name='generate-questions'),
    path('get/<int:topic_id>/', GetQuestionsByTopicView.as_view(), name='get-questions'),
    
    # ✅ --- ADD THIS NEW URL --- ✅
    path('submit-response/', SaveQuizResponseView.as_view(), name='submit-quiz-response'),
]