from django.db import models
from django.contrib.auth.models import User

class Material(models.Model):
    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=100)  # removed unique=True so you can upload multiple materials for same subject
    drive_file_id = models.CharField(max_length=255, unique=True)
    view_url = models.URLField(max_length=500, blank=True, null=True)
    download_url = models.URLField(max_length=500, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.subject})"


class MaterialAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'material')

    def __str__(self):
        return f"{self.user.username} → {self.material.title}"
