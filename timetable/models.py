from django.db import models
from django.conf import settings
from materials.models import Material  # ✅ Fixed import

class StudyPlanRequest(models.Model):
    """
    Stores the user's form input for generating a study plan.
    """
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
    """
    Represents the generated study plan itself, linked to the initial request.
    """
    request = models.OneToOneField(
        StudyPlanRequest,
        on_delete=models.CASCADE,
        related_name='plan'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Study Plan for {self.request.user.username}"


class DailyTask(models.Model):
    """
    Stores specific tasks for each day within a study plan.
    """
    study_plan = models.ForeignKey(
        StudyPlan,
        on_delete=models.CASCADE,
        related_name='daily_tasks'
    )
    day = models.PositiveIntegerField()
    focus_subject = models.CharField(max_length=255)
    topics = models.TextField()
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('study_plan', 'day')
        ordering = ['day']

    def __str__(self):
        return f"Day {self.day}: {self.focus_subject}"
