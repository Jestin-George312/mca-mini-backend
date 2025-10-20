# materials/urls.py

from django.urls import path
from .views import UploadMaterialView, MaterialListView

urlpatterns = [
    path('', UploadMaterialView.as_view(), name='upload-material'),
     path('list/', MaterialListView.as_view(), name='list-materials'),
]
