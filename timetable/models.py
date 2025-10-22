# timetable/models.py

from django.db import models
from django.conf import settings
from materials.models import Material

# ... StudyPlanRequest and StudyPlan models are unchanged ...

class StudyPlanRequest(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='study_plan_requests'
    )
    materials = models.ManyToManyField(
        Material,
        related_name='study_plan_requests'
    )
    total_days = models.PositiveIntegerField(default=7)
    hours_per_day = models.PositiveIntegerField(default=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Plan request by {self.user.username} ({self.created_at.strftime('%Y-%m-%d')})"


class StudyPlan(models.Model):
    request = models.OneToOneField(
        StudyPlanRequest,
        on_delete=models.CASCADE,
        related_name='plan'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Study Plan for {self.request.user.username}"


# ✅ TimeSlotTask model is MODIFIED
class TimeSlotTask(models.Model):
    study_plan = models.ForeignKey(
        StudyPlan,
        on_delete=models.CASCADE,
        related_name='time_slot_tasks'
    )
    day = models.PositiveIntegerField()
    # ✅ RENAMED this field
    duration = models.CharField(max_length=100)  # e.g., "2 hours", "1.5 hours"
    subject = models.CharField(max_length=255)
    topics = models.TextField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['day', 'id'] 

    def __str__(self):
        # ✅ Updated __str__
        return f"Day {self.day} ({self.duration}): {self.subject}"