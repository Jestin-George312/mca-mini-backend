from django.contrib import admin
from .models import Topic

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    """
    Configures the admin interface for the Topic model.
    """
    list_display = ('topic_name', 'material', 'sequence_number', 'difficulty_class', 'difficulty_score')
    list_filter = ('difficulty_class', 'material__subject')
    search_fields = ('topic_name', 'summary', 'material__title')
    ordering = ('material', 'sequence_number')
    list_per_page = 25
    readonly_fields = ('material',)
