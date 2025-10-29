from django.contrib import admin
from .models import Material,MaterialAccess
# Register your models here.
admin.site.register(Material)
admin.site.register(MaterialAccess)
  # Add your models here to register them with the admin site