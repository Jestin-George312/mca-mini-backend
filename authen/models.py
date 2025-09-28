
from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.utils.timezone import now

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.user.username



    





"""class UserProfile(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username"""