
# timetable/urls.py
from django.urls import path
# ✅ Import the new view
from .views import GenerateStudyPlanView, StudyPlanDetailView, UpdateStudyPlanView

urlpatterns = [
    path('generate-plan/', GenerateStudyPlanView.as_view(), name='generate-study-plan'),
    
    # ✅ Add the new URL pattern for fetching the plan
    path('my-plan/', StudyPlanDetailView.as_view(), name='get-study-plan'),
    path('update-plan/', UpdateStudyPlanView.as_view(), name='update-study-plan'),
]