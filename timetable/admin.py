from django.contrib import admin
from .models import StudyPlanRequest, StudyPlan, TimeSlotTask
# Register your models here.
admin.site.register(StudyPlanRequest)
admin.site.register(StudyPlan)
admin.site.register(TimeSlotTask)  # Add your models here to register them with the admin site