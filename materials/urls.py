# materials/urls.py

from django.urls import path
from .views import UploadMaterialView, MaterialListView, DeleteMaterialView

urlpatterns = [
    path('', UploadMaterialView.as_view(), name='upload-material'),
     path('list/', MaterialListView.as_view(), name='list-materials'),
     path('delete/<int:material_id>/', DeleteMaterialView.as_view(), name='delete-material'),
]
