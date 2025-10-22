from django.urls import path
from . import views

app_name = 'topic_analysis'

urlpatterns = [
    # URL to trigger the analysis for a material with a given ID.
    # e.g., POST /topic-analysis/analyze/123/
    path('analyze/<int:material_id>/', views.trigger_analysis, name='trigger_analysis'),
    path('topics/<int:material_id>/', views.get_material_topics, name='get_material_topics'),
]
