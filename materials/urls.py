# materials/urls.py

from django.urls import path
from .views import UploadMaterialView

urlpatterns = [
    path('', UploadMaterialView.as_view(), name='upload-material'),
]
