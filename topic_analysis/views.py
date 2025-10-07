from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from materials.models import Material
from .analysis_service import analyze_material

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
