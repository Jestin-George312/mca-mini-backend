from django.db import models
from materials.models import Material

class Topic(models.Model):
    """
    Represents a single topic identified within a Material (PDF).
    
    Stores the topic's name, summary, difficulty assessment, and its
    order of appearance within the source material.
    """
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    material = models.ForeignKey(
        Material, 
        related_name='topics', 
        on_delete=models.CASCADE,
        help_text="The material this topic belongs to."
    )
    topic_name = models.CharField(max_length=255)
    difficulty_score = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        help_text="Difficulty score from 1.00 to 10.00"
    )
    difficulty_class = models.CharField(
        max_length=10, 
        choices=DIFFICULTY_CHOICES
    )
    summary = models.TextField(
        help_text="A short summary of the topic's content."
    )
    sequence_number = models.PositiveIntegerField(
        help_text="The order in which the topic appears in the material."
    )

    class Meta:
        # Order topics by their sequence number by default
        ordering = ['sequence_number']
        # Ensure that each sequence number is unique for a given material
        unique_together = ('material', 'sequence_number')

    def __str__(self):
        return f"{self.sequence_number}. {self.topic_name} ({self.get_difficulty_class_display()}) for '{self.material.title}'"
