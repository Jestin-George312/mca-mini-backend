
# timetable/urls.py
from django.urls import path
# ✅ Import the new view
from .views import GenerateStudyPlanView, StudyPlanDetailView

urlpatterns = [
    path('generate-plan/', GenerateStudyPlanView.as_view(), name='generate-study-plan'),
    
    # ✅ Add the new URL pattern for fetching the plan
    path('my-plan/', StudyPlanDetailView.as_view(), name='get-study-plan'),
]