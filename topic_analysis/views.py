from django.http import JsonResponse
from django.views.decorators.http import require_POST,require_GET
from django.contrib.auth.decorators import login_required
from materials.models import Material
from .analysis_service import analyze_material
from .models import Topic

# For a production setup, you would use a task queue like Celery
# from .tasks import run_analysis_task

@login_required
@require_POST
def trigger_analysis(request, material_id):
    """
    API endpoint to trigger the analysis of a material.

    This view is the entry point for the analysis process.
    IMPORTANT: For demonstration, it runs the analysis synchronously, which will
    block the request and can time out for large files. In a production 
    environment, you should delegate this to a background task runner.
    """
    try:
        # A real implementation should include an authorization check, e.g.,
        # ensuring the request.user has permission to analyze this material.
        Material.objects.get(pk=material_id)
    except Material.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Material not found.'}, status=404)
    
    # --- PRODUCTION APPROACH (using Celery) ---
    # 1. Define a task in a `tasks.py` file: `@shared_task def run_analysis_task(material_id): analyze_material(material_id)`
    # 2. Call the task here: `run_analysis_task.delay(material_id)`
    # 3. Return an immediate response: `return JsonResponse({'status': 'queued', 'message': 'Analysis has been started.'})`
    
    # --- DEMONSTRATION APPROACH (Synchronous) ---
    try:
        analyze_material(material_id)
        message = f'Analysis for material {material_id} completed successfully.'
        return JsonResponse({'status': 'success', 'message': message})
    except Exception as e:
        # In a real app, you would log this exception.
        print(f"An error occurred during analysis: {e}")
        return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred during analysis.'}, status=500)


@require_GET
def get_material_topics(request, material_id):
    """
    Fetch all topics related to a specific material.
    Returns a JSON list of topics with their details.
    """
    try:
        material = Material.objects.get(pk=material_id)
    except Material.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Material not found.'}, status=404)

    topics = Topic.objects.filter(material=material).order_by('sequence_number')

    topic_data = [
        {
            'id': topic.id,
            'topic_name': topic.topic_name,
            'difficulty_score': float(topic.difficulty_score),
            'difficulty_class': topic.difficulty_class,
            'summary': topic.summary,
            'sequence_number': topic.sequence_number
        }
        for topic in topics
    ]

    return JsonResponse({
        'status': 'success',
        'material_title': material.title,
        'total_topics': len(topic_data),
        'topics': topic_data
    }, status=200)