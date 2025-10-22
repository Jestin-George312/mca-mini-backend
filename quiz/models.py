# quiz/models.py

from django.db import models
from topic_analysis.models import Topic
from django.conf import settings # ✅ Import settings

class QuizQuestion(models.Model):
    # ... your existing QuizQuestion model ...
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=255, blank=True, null=True)
    option_b = models.CharField(max_length=255, blank=True, null=True)
    option_c = models.CharField(max_length=255, blank=True, null=True)
    option_d = models.CharField(max_length=255, blank=True, null=True)
    correct_option = models.CharField(max_length=1, blank=True, null=True)
    question_type = models.CharField(max_length=50, default='mcq')
    difficulty = models.CharField(max_length=20, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text[:80]

# ✅ --- ADD THIS NEW MODEL --- ✅
class QuizResult(models.Model):
    """
    Stores the result of a single quiz taken by a user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='quiz_results'
    )
    topic = models.ForeignKey(
        Topic, 
        on_delete=models.CASCADE, 
        related_name='quiz_results'
    )
    score = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quiz result for {self.user.username} on {self.topic.topic_name}"

    class Meta:
        ordering = ['-timestamp']